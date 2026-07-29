import asyncio
import logging
from typing import Optional

import httpx

from bot.ai.prompts import SYSTEM_PROMPT, PERSONALIZATION_PROMPT
from bot.config import settings

logger = logging.getLogger(__name__)


class AIError(Exception):
    pass


class AIClient:
    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.openai_base_url,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate_response(
        self,
        user_name: str | None,
        user_age: int | None,
        user_goal: str | None,
        history: list[dict[str, str]],
        user_message: str,
    ) -> str:
        client = await self._get_client()

        system_content = SYSTEM_PROMPT

        if user_name or user_age or user_goal:
            profile = PERSONALIZATION_PROMPT.format(
                first_name=user_name or "неизвестно",
                age=str(user_age) if user_age else "неизвестно",
                goal=user_goal or "не указана",
                history="\n".join(f"{msg['role']}: {msg['content']}" for msg in history[-10:]),
            )
            system_content += "\n\n" + profile

        messages = [{"role": "system", "content": system_content}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_message})

        logger.info("Sending request to AI API", extra={"model": settings.openai_model, "messages_count": len(messages)})

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await client.post(
                    "/chat/completions",
                    json={
                        "model": settings.openai_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)

                logger.info("Received AI response", extra={"tokens": tokens})
                return content.strip()

            except httpx.TimeoutException:
                logger.warning(f"AI API timeout, attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise AIError("Сервис временно недоступен, попробуйте позже")
                import asyncio
                await asyncio.sleep(base_delay * (2 ** attempt))

            except httpx.HTTPStatusError as e:
                logger.error(f"AI API HTTP error: {e.response.status_code}")
                if e.response.status_code >= 500:
                    if attempt == max_retries - 1:
                        raise AIError("Сервис временно недоступен, попробуйте позже")
                    import asyncio
                    await asyncio.sleep(base_delay * (2 ** attempt))
                else:
                    raise AIError("Не удалось обработать запрос")

            except Exception as e:
                logger.error("AI API error", exc_info=e)
                raise AIError("Не удалось обработать запрос")

        raise AIError("Сервис временно недоступен, попробуйте позже")


_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


async def close_ai_client() -> None:
    global _ai_client
    if _ai_client:
        await _ai_client.close()
        _ai_client = None
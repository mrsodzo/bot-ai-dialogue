import logging
import time
from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start_time = time.time()

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            logger.info("Message received", extra={"user_id": user_id, "text": event.text[:100] if event.text else None})
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            logger.info("Callback received", extra={"user_id": user_id, "data": event.data})

        try:
            result = await handler(event, data)
            duration = time.time() - start_time
            logger.info("Handler completed", extra={"user_id": user_id, "duration_ms": round(duration * 1000, 2)})
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Handler error", extra={"user_id": user_id, "duration_ms": round(duration * 1000, 2)}, exc_info=e)
            raise
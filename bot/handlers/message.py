from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.queries import get_user, update_user, add_message, get_user_history
from bot.ai import get_ai_client, AIError, SYSTEM_PROMPT, PERSONALIZATION_PROMPT
from bot.config import config

router = Router()


@router.message(F.text)
async def handle_message(message: Message, session: AsyncSession) -> None:
    user = await get_user(session, message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, начните с команды /start")
        return

    await add_message(session, user.id, "user", message.text)

    history = await get_user_history(session, user.id, config.max_history_messages)

    history_text = "\n".join(
        f"{'👤' if m.role == 'user' else '🤖'} {m.content}"
        for m in history
    ) if history else "История пуста"

    name = user.name or "неизвестно"
    age = user.age or "неизвестно"
    goal = user.goal or "неизвестно"

    personalization = PERSONALIZATION_PROMPT.format(
        first_name=name,
        age=age,
        goal=goal,
        max_history=config.max_history_messages,
        history=history_text,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": personalization},
        {"role": "user", "content": message.text},
    ]

    ai_client = get_ai_client()

    try:
        response, tokens = await ai_client.chat_completion(messages)
        await add_message(session, user.id, "assistant", response)
        await message.answer(response)

    except AIError as e:
        await message.answer(str(e))

    except Exception:
        await message.answer("Произошла ошибка. Попробуйте позже.")
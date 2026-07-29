import logging
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import get_or_create_user, update_user_stage, update_user_profile, add_message, get_user_history
from bot.ai import get_ai_client, AIError

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text)
async def handle_message(message: Message, session: AsyncSession) -> None:
    if not message.text or message.text.startswith("/"):
        return

    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )

    await add_message(session, user.telegram_id, "user", message.text)

    if user.stage == "start":
        await update_user_stage(session, user, "name")
        await session.flush()

        await message.answer(f"Приятно познакомиться, {message.text}! 😊\n\nСколько тебе лет?")
        await add_message(session, user.telegram_id, "assistant", f"Приятно познакомиться, {message.text}! 😊\n\nСколько тебе лет?")
        return

    if user.stage == "name":
        await update_user_profile(session, user, name=message.text)
        await update_user_stage(session, user, "age")
        await session.flush()

        await message.answer(f"Отлично, {message.text}! Сколько тебе лет?")
        await add_message(session, user.telegram_id, "assistant", f"Отлично, {message.text}! Сколько тебе лет?")
        return

    if user.stage == "age":
        try:
            age = int(message.text)
            if age < 1 or age > 120:
                raise ValueError
        except ValueError:
            await message.answer("Пожалуйста, введи корректный возраст (число от 1 до 120).")
            return

        await update_user_profile(session, user, age=age)
        await update_user_stage(session, user, "goal")
        await session.flush()

        await message.answer(f"Понял, {age} лет. Какая у тебя цель или зачем ты обратился ко мне?")
        await add_message(session, user.telegram_id, "assistant", f"Понял, {age} лет. Какая у тебя цель или зачем ты обратился ко мне?")
        return

    if user.stage == "goal":
        await update_user_profile(session, user, goal=message.text)
        await update_user_stage(session, user, "active")
        await session.flush()

        await message.answer(
            f"Супер! Цель: «{message.text}». Теперь ты можешь задать мне любой вопрос!",
            reply_markup=None,
        )
        await add_message(session, user.telegram_id, "assistant", f"Супер! Цель: «{message.text}». Теперь ты можешь задать мне любой вопрос!")
        return

    history = await get_user_history(session, user.telegram_id, limit=10)
    history_messages = [{"role": msg.role, "content": msg.content} for msg in history]

    ai_client = get_ai_client()
    try:
        response = await ai_client.generate_response(
            user_name=user.name,
            user_age=user.age,
            user_goal=user.goal,
            history=history_messages,
            user_message=message.text,
        )
    except AIError as e:
        response = str(e)

    await message.answer(response)
    await add_message(session, user.telegram_id, "assistant", response)
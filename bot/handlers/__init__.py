import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import get_or_create_user, update_user_stage, update_user_profile, reset_user, add_message, get_user_history
from bot.ai import get_ai_client, AIError
from bot.utils import get_main_keyboard, get_cancel_keyboard, get_remove_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )

    logger.info(f"User {user.telegram_id} started bot, stage: {user.stage}")

    if user.stage == "start":
        await update_user_stage(session, user, "ask_name")
        await message.answer(
            "Привет! 👋 Я — твой AI-помощник. Давай познакомимся!\n\nКак тебя зовут?",
            reply_markup=get_cancel_keyboard(),
        )
    elif user.stage == "ask_name":
        await message.answer(
            "Как тебя зовут?",
            reply_markup=get_cancel_keyboard(),
        )
    elif user.stage == "ask_age":
        await message.answer(
            f"Приятно познакомиться, {user.name}!\n\nСколько тебе лет?",
            reply_markup=get_cancel_keyboard(),
        )
    elif user.stage == "ask_goal":
        await message.answer(
            f"Принято, {user.name}, {user.age} лет.\n\nКакая у тебя цель? Чем могу помочь?",
            reply_markup=get_cancel_keyboard(),
        )
    else:
        await message.answer(
            f"С возвращением, {user.name}! 😊\n\nО чём хочешь поговорить?",
            reply_markup=get_main_keyboard(),
        )


@router.message(Command("reset"))
async def cmd_reset(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )

    await reset_user(session, user)
    logger.info(f"User {user.telegram_id} reset profile")

    await message.answer(
        "Профиль и история диалога сброшены. 👋\n\nЕсли захочешь поговорить — просто напиши /start",
        reply_markup=get_remove_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "🤖 <b>AI Dialogue Bot</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — начать диалог\n"
        "/reset — сбросить профиль и историю\n"
        "/help — эта справка\n\n"
        "Бот запоминает твое имя, возраст и цель, чтобы отвечать персонализированно.",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )

    if user.stage in ("ask_name", "ask_age", "ask_goal"):
        await update_user_stage(session, user, "start")
        await message.answer(
            "Хорошо, давай начнём сначала. Напиши /start",
            reply_markup=get_remove_keyboard(),
        )
    else:
        await message.answer("Нечего отменять.", reply_markup=get_main_keyboard())


@router.message(F.text)
async def handle_message(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )

    if user.stage == "ask_name":
        await update_user_profile(session, user, name=message.text.strip())
        await update_user_stage(session, user, "ask_age")
        await message.answer(
            f"Приятно познакомиться, {user.name}!\n\nСколько тебе лет?",
            reply_markup=get_cancel_keyboard(),
        )
        return

    if user.stage == "ask_age":
        try:
            age = int(message.text.strip())
            if age < 1 or age > 120:
                raise ValueError
        except ValueError:
            await message.answer("Пожалуйста, введи корректный возраст (число от 1 до 120):")
            return

        await update_user_profile(session, user, age=age)
        await update_user_stage(session, user, "ask_goal")
        await message.answer(
            f"Принято, {user.name}, {user.age} лет.\n\nКакая у тебя цель? Чем могу помочь?",
            reply_markup=get_cancel_keyboard(),
        )
        return

    if user.stage == "ask_goal":
        goal = message.text.strip()
        await update_user_profile(session, user, goal=goal)
        await update_user_stage(session, user, "chat")
        await message.answer(
            f"Понял, цель: «{goal}».\n\nТеперь можешь задать любой вопрос! 💬",
            reply_markup=get_main_keyboard(),
        )
        return

    if user.stage == "chat":
        await add_message(session, user.telegram_id, "user", message.text)

        history = await get_user_history(session, user.telegram_id)
        history_dicts = [{"role": m.role, "content": m.content} for m in history]

        ai_client = get_ai_client()
        try:
            response = await ai_client.generate_response(
                user_name=user.name,
                user_age=user.age,
                user_goal=user.goal,
                history=history_dicts,
                user_message=message.text,
            )
        except AIError as e:
            await message.answer(str(e))
            return

        await add_message(session, user.telegram_id, "assistant", response)
        await message.answer(response, reply_markup=get_main_keyboard())
        return

    await message.answer("Напиши /start, чтобы начать.", reply_markup=get_main_keyboard())
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import get_or_create_user, update_user_stage, update_user_profile, reset_user, add_message, get_user_history
from bot.ai import get_ai_client, AIError
from bot.utils.keyboards import get_main_keyboard, get_cancel_keyboard

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

    if user.stage != "start":
        await update_user_stage(session, user, "start")
        await session.flush()

    await add_message(session, user.telegram_id, "user", "/start")

    welcome_text = (
        f"Привет, {user.first_name or 'друг'}! 👋\n\n"
        "Я — твой AI-помощник. Давайте познакомимся!\n"
        "Как к тебе можно обращаться?"
    )

    await message.answer(welcome_text, reply_markup=get_cancel_keyboard())
    await add_message(session, user.telegram_id, "assistant", welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession) -> None:
    help_text = (
        "🤖 <b>Помощник</b>\n\n"
        "Команды:\n"
        "/start — начать диалог заново\n"
        "/help — эта справка\n"
        "/reset — сбросить профиль и историю\n\n"
        "Просто пиши мне сообщения — я отвечу, учитывая твой профиль и историю диалога."
    )
    await message.answer(help_text, parse_mode="HTML")
    await add_message(session, message.from_user.id, "user", "/help")
    await add_message(session, message.from_user.id, "assistant", help_text)


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
    await session.flush()

    await message.answer(
        "Хорошо, я сбросил твой профиль и историю. Давай начнём заново!\n\nКак к тебе можно обращаться?",
        reply_markup=get_cancel_keyboard(),
    )
    await add_message(session, user.telegram_id, "user", "/reset")
    await add_message(session, user.telegram_id, "assistant", "Хорошо, я сбросил твой профиль и историю. Давай начнём заново!\n\nКак к тебе можно обращаться?")


@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )

    if user.stage in ("name", "age", "goal"):
        await update_user_stage(session, user, "start")
        await session.flush()

    await message.answer("Хорошо, давай начнём сначала. Как к тебе можно обращаться?", reply_markup=get_cancel_keyboard())
    await add_message(session, user.telegram_id, "user", "❌ Отмена")
    await add_message(session, user.telegram_id, "assistant", "Хорошо, давай начнём сначала. Как к тебе можно обращаться?")
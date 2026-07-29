from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.db.queries import get_or_create_user, update_user_stage, get_user
from bot.handlers.keyboards import get_start_keyboard

router = Router()


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext, session) -> None:
    user = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    if user.name:
        await message.answer(
            f"Привет, {user.name}! 👋\n"
            f"Рад тебя снова видеть. Чем могу помочь?",
            reply_markup=get_start_keyboard(),
        )
    else:
        await message.answer(
            "Привет! 👋 Я — твой AI-помощник.\n\n"
            "Давайте познакомимся. Как к вам можно обращаться?",
        )
        await update_user_stage(session, user, "waiting_name")


@router.message(Command("reset"))
async def reset_cmd(message: Message, state: FSMContext, session) -> None:
    user = await get_user(session, message.from_user.id)
    if not user:
        await message.answer("Вы еще не начинали диалог. Напишите /start")
        return

    from bot.db.queries import reset_user
    await reset_user(session, user)
    await state.clear()
    await message.answer("Диалог сброшен. До свидания! 👋\n\nНапишите /start, чтобы начать заново.")


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "🤖 <b>Доступные команды:</b>\n\n"
        "/start — начать диалог\n"
        "/reset — сбросить профиль и историю\n"
        "/help — показать эту справку\n\n"
        "Просто пишите сообщения, и я отвечу с учётом вашего профиля и контекста диалога.",
        parse_mode="HTML",
    )
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/reset")],
            [KeyboardButton(text="/help")],
        ],
        resize_keyboard=True,
    )


def get_profile_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Изменить имя")],
            [KeyboardButton(text="Изменить возраст")],
            [KeyboardButton(text="Изменить цель")],
            [KeyboardButton(text="/reset")],
        ],
        resize_keyboard=True,
    )
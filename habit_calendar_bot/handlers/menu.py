from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отметить сегодня")],
            [KeyboardButton(text="Календарь"), KeyboardButton(text="Прогресс")],
            [KeyboardButton(text="Награды"), KeyboardButton(text="Настройки")],
        ],
        resize_keyboard=True,
    )

# bot/keyboards/finance.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.keyboards.base import main_menu

# Клавиатура с отменой и пропуском
description_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пропустить")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
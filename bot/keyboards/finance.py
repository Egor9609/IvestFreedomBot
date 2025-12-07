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

expense_cancel_keyboard = cancel_keyboard
expense_description_keyboard = description_keyboard

report_period_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Сегодня")],
        [KeyboardButton(text="📅 Неделя"), KeyboardButton(text="📅 Месяц")],
        [KeyboardButton(text="📅 Год")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

report_detail_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📤 Экспорт в Excel")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
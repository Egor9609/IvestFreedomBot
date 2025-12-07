# bot/keyboards/debts.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

debts_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить долг"), KeyboardButton(text="📋 Список долгов")],
        [KeyboardButton(text="💰 Внести платеж"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

debts_cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)
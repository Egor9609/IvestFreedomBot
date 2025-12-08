# bot/keyboards/bills.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bills_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить счёт"), KeyboardButton(text="📋 Список счетов")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

bills_cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для выбора привязки к долгу
link_debt_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔗 Привязать к долгу")],
        [KeyboardButton(text="🚫 Не привязывать")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
# bot/keyboards/debts.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

debts_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить долг"), KeyboardButton(text="📋 Список долгов")],
        [KeyboardButton(text="💳 Внести платёж"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)
# Клавиатура отмены
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)
debts_cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

due_date_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Через неделю"), KeyboardButton(text="📅 Через месяц")],
        [KeyboardButton(text="📅 Через 3 месяца"), KeyboardButton(text="📅 Через полгода")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

category_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏦 Кредит"), KeyboardButton(text="👤 Долг другу")],
        [KeyboardButton(text="🛒 Рассрочка"), KeyboardButton(text="🏠 Ипотека")],
        [KeyboardButton(text="📱 Техника"), KeyboardButton(text="📝 Другое")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
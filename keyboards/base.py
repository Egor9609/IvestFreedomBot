# bot/keyboards/base.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = Reply_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Доходы"), KeyboardButton(text="💸 Расходы")],
        [KeyboardButton(text="💳 Долги"), KeyboardButton(text="🧾 Счета")],
        [KeyboardButton(text="📊 Отчёты")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
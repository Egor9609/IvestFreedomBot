# bot/keyboards/bills.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bills_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить счёт"), KeyboardButton(text="📋 Список счетов")],
        [KeyboardButton(text="💳 Оплатить счёт")],
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

due_date_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Через неделю"), KeyboardButton(text="📅 Через месяц")],
        [KeyboardButton(text="📅 Через 3 месяца"), KeyboardButton(text="📅 Через полгода")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

schedule_selection_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 До конца погашения")],
        [KeyboardButton(text="⚙️ Настроить график вручную")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

payment_frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📆 Каждую неделю")],
        [KeyboardButton(text="📆 Каждые 2 недели")],
        [KeyboardButton(text="📆 Каждый месяц")],
        [KeyboardButton(text="📆 Квартал (3 мес)")],
        [KeyboardButton(text="📆 Полгода")],
        [KeyboardButton(text="📆 Год")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

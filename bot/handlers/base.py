# bot/handlers/base.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from bot.keyboards.base import main_menu
from bot.database.repository import UserRepository
from bot.database.session import get_session
from bot.keyboards.debts import debts_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Получаем сессию и работаем с репозиторием
    async for session in get_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )

    await message.answer(
        "Привет! Я FinBot — твой финансовый помощник. Выбери действие:",
        reply_markup=main_menu
    )

@router.message(F.text == "💳 Долги")
async def btn_debts(message: Message):
    await message.answer("💳 Управление долгами:", reply_markup=debts_menu)
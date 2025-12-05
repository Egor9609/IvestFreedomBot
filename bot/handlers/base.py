# bot/handlers/base.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from bot.keyboards.base import main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я FinBot — твой финансовый помощник. Выбери действие:",
        reply_markup=main_menu
    )
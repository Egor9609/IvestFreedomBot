# bot/handlers/debts/list.py

from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.debts import debts_menu
from bot.keyboards.base import main_menu
from services.debt_service import DebtService

router = Router()

@router.message(F.text == "📋 Список долгов")
async def show_debts_list(message: Message):
    debts = await DebtService.get_active_debts(message.from_user.id)

    if not debts:
        await message.answer("У вас нет активных долгов.", reply_markup=debts_menu)
        return

    text = "📋 Ваши долги:\n\n"
    for d in debts:
        paid = d.total_amount - d.remaining_amount
        text += (
            f"ID: {d.id}\n"
            f"Описание: {d.description}\n"
            f"Сумма: {d.total_amount:,.2f} руб.\n"
            f"Оплачено: {paid:,.2f} руб.\n"
            f"Осталось: {d.remaining_amount:,.2f} руб.\n"
            f"{'—' * 20}\n"
        )

    await message.answer(text, reply_markup=debts_menu)
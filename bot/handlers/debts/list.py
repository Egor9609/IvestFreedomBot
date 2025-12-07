# bot/handlers/debts/list.py

from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.debts import debts_menu
from bot.keyboards.base import main_menu
from services.debt_service import DebtService
from datetime import datetime, date

router = Router()

@router.message(F.text == "📋 Список долгов")
async def show_debts_list(message: Message):
    debts = await DebtService.get_active_debts(message.from_user.id)

    if not debts:
        await message.answer("У вас нет активных долгов.", reply_markup=debts_menu)
        return

    text = "📋 Ваши активные долги:\n\n"
    total_remaining = 0

    for i, d in enumerate(debts, 1):
        days_left = (d.due_date - date.today()).days

        # Статус
        if days_left <= 7:
            status = "🔥 Срочно"
        else:
            status = "✅ В порядке"

        # Категория
        category = d.category if d.category != "Другое" else "Другое"
        if category == "Другое" and d.note:
            category = f"Другое ({d.note})"

        text += (
            f"{i}. {d.description}\n"
            f"   💰 {d.remaining_amount:,.2f} / {d.total_amount:,.2f} руб.\n"
            f"   📅 {d.due_date.strftime('%d.%m.%Y')}\n"
            f"   🏷️ {category}\n"
            f"   ⏱️ {status} ({days_left} дней)\n\n"
        )
        total_remaining += d.remaining_amount

    text += f"📊 Итого к погашению: {total_remaining:,.2f} руб."
    await message.answer(text, reply_markup=debts_menu)
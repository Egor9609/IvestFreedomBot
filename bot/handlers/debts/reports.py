# bot/handlers/debts/reports.py

from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.debts import debts_menu
from services.debt_service import DebtService
from datetime import date

router = Router()

@router.message(F.text == "📊 Статистика")
async def show_debt_stats(message: Message):
    stats = await DebtService.get_debt_statistics(message.from_user.id)

    if not stats or stats["total_debts"] == 0:
        await message.answer("У вас пока нет долгов.", reply_markup=debts_menu)
        return

    # Основная статистика
    text = "📊 Статистика по долгам\n\n"
    text += f"📈 Всего долгов: {stats['total_debts']}\n"
    text += f"💰 Общая сумма: {stats['total_amount']:,.2f} руб.\n"
    text += f"💵 Осталось выплатить: {stats['remaining']:,.2f} руб.\n"
    text += f"✅ Уже выплачено: {stats['paid']:,.2f} руб.\n"
    text += f"⚠️ Просрочено: {stats['overdue_count']} на сумму {stats['overdue_amount']:,.2f} руб.\n\n"

    # По категориям
    text += "По категориям:\n"
    for cat, data in stats["by_category"].items():
        pct = (data["paid"] / data["total"] * 100) if data["total"] > 0 else 0
        text += f"  • {cat}: {data['count']} шт., {data['total']:,.2f} руб. ({pct:.1f}% выплачено)\n"

    # Ближайшие сроки
    text += "\nБлижайшие сроки:\n"
    for d in stats["nearest"]:
        days = (d.due_date - date.today()).days
        if days < 0:
            days_desc = "просрочен"
        else:
            days_desc = f"через {days} дн."
        text += f"  • {d.description}: {d.remaining_amount:,.2f} руб. ({days_desc})\n"

    await message.answer(text, reply_markup=debts_menu)
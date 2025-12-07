# bot/handlers/finance/reports.py
from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.finance import report_period_keyboard
from bot.keyboards.base import main_menu
from services.finance_service import FinanceService
from bot.logger import logger

router = Router()

@router.message(F.text == "📊 Отчёты")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период для отчёта:", reply_markup=report_period_keyboard)

@router.message(F.text.in_({"📅 Сегодня", "📅 Неделя", "📅 Месяц", "📅 Год"}))
async def handle_report_period(message: Message):
    period_map = {
        "📅 Сегодня": "day",
        "📅 Неделя": "week",
        "📅 Месяц": "month",
        "📅 Год": "year"
    }
    period = period_map[message.text]

    result = await FinanceService.get_balance_report(
        telegram_id=message.from_user.id,
        period=period
    )

    if not result.get("success"):
        await message.answer("Ошибка при формировании отчёта.", reply_markup=main_menu)
        return

    # Форматируем числа с разделителями тысяч и 2 знаками после запятой
    def format_money(x):
        if x is None:
            x = 0
        # Преобразуем в float, чтобы унифицировать тип
        x = float(x)
        if x.is_integer():
            return f"{int(x):,} руб.".replace(",", " ")
        else:
            return f"{x:,.2f} руб.".replace(",", " ")

    response = (
        f"📊 Отчет за {result['title']}\n\n"
        f"📈 Доходы: {format_money(result['income'])}\n"
        f"📉 Расходы: {format_money(result['expense'])}\n"
        f"💰 Баланс: {format_money(result['balance'])}\n\n"
        f"Количество операций: {result['count']}"
    )
    await message.answer(response, reply_markup=main_menu)

@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu)
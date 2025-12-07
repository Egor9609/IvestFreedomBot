# bot/handlers/finance/reports.py
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.keyboards.finance import report_period_keyboard, report_detail_keyboard
from bot.keyboards.base import main_menu
from services.finance_service import FinanceService
from services.export_service import ExportService
from bot.logger import logger

router = Router()

class ReportStates(StatesGroup):
    viewing_report = State()

@router.message(F.text == "📊 Отчёты")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период для отчёта:", reply_markup=report_period_keyboard)

@router.message(F.text.in_({"📅 Сегодня", "📅 Неделя", "📅 Месяц", "📅 Год"}))
async def handle_report_period(message: Message, state: FSMContext):
    period_map = {
        "📅 Сегодня": "day",
        "📅 Неделя": "week",
        "📅 Месяц": "month",
        "📅 Год": "year"
    }
    period_key = message.text
    period = period_map[period_key]

    result = await FinanceService.get_balance_report(
        telegram_id=message.from_user.id,
        period=period
    )

    if not result.get("success"):
        await message.answer("Ошибка при формировании отчёта.", reply_markup=main_menu)
        return

    def format_money(x):
        if x is None:
            x = 0
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

    # ✅ Сохраняем период и устанавливаем состояние
    await state.update_data(report_period=period)
    await state.set_state(ReportStates.viewing_report)

    # ✅ Используем клавиатуру с кнопкой "Экспорт"
    await message.answer(response, reply_markup=report_detail_keyboard)


@router.message(ReportStates.viewing_report, F.text == "📤 Экспорт в Excel")
async def export_report_excel(message: Message, state: FSMContext):
    data = await state.get_data()
    period = data.get("report_period")

    if not period:
        await message.answer("Ошибка: период не найден.", reply_markup=main_menu)
        await state.clear()
        return

    # Генерируем Excel
    result = await ExportService.export_transactions_to_excel(
        telegram_id=message.from_user.id,
        period=period
    )

    if result is None:
        await message.answer("Нет данных для экспорта за этот период.", reply_markup=main_menu)
    else:
        excel_file, filename = result
        excel_bytes = excel_file.getvalue()

        document = BufferedInputFile(file=excel_bytes, filename=filename)
        await message.answer_document(document=document, caption="📄 Ваш финансовый отчёт.")
        await message.answer("Главное меню:", reply_markup=main_menu)

    await state.clear()

@router.message(ReportStates.viewing_report, F.text == "🔙 Назад")
async def back_from_report_detail(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu)


@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu)
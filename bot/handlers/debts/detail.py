# bot/handlers/debts/detail.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import date

from bot.states.debt_states import DebtListStates, DebtDetailStates
from bot.services.debt_service import DebtService
from bot.keyboards.debts import debts_menu
from bot.handlers.debts.list import show_debts_list

router = Router()

# Клавиатура управления долгом
def get_debt_detail_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Внести платёж")],
            [KeyboardButton(text="✏️ Редактировать"), KeyboardButton(text="✅ Закрыть долг")],
            [KeyboardButton(text="❌ Удалить"), KeyboardButton(text="📋 Назад к списку")]
        ],
        resize_keyboard=True
    )

@router.message(DebtListStates.selecting_debt)
async def show_debt_detail(message: Message, state: FSMContext):
    if message.text == "📋 Назад":
        await message.answer("Главное меню долгов:", reply_markup=debts_menu)
        await state.clear()
        return

    data = await state.get_data()
    debt_id = data["debt_map"].get(message.text)
    if not debt_id:
        await message.answer("Выберите долг из списка.")
        return

    debt = await DebtService.get_debt_by_id(debt_id)
    if not debt:
        await message.answer("Долг не найден.")
        return

    # Расчёт
    paid = debt.total_amount - debt.remaining_amount
    progress_pct = (paid / debt.total_amount * 100) if debt.total_amount > 0 else 0
    progress_bar = "█" * int(progress_pct // 10) + "░" * (10 - int(progress_pct // 10))
    days_left = (debt.due_date - date.today()).days
    status = f"{days_left} дней" if days_left >= 0 else "ПРОСРОЧЕН"

    response = (
        "📄 Детали долга\n\n"
        f"🏦 Название: {debt.description}\n"
        f"💰 Общая сумма: {debt.total_amount:,.2f} руб.\n"
        f"💵 Остаток: {debt.remaining_amount:,.2f} руб.\n"
        f"📈 Погашено: {paid:,.2f} руб.\n"
        f"📊 Прогресс: {progress_pct:.1f}%\n"
        f"   {progress_bar}\n"
        f"📅 Дата погашения: {debt.due_date.strftime('%d.%m.%Y')}\n"
        f"⏱️ Дней осталось: {status}\n"
        f"🏷️ Категория: {debt.category}\n"
        f"📝 Создан: {debt.created_at.strftime('%d.%m.%Y')}"
    )
    if debt.note:
        response += f"\n📝 Примечание: {debt.note}"

    await state.update_data(current_debt_id=debt_id)
    await state.set_state(DebtDetailStates.viewing_detail)
    await message.answer(response, reply_markup=get_debt_detail_keyboard())

# === Закрыть долг ===
@router.message(F.text == "✅ Закрыть долг")
async def close_debt(message: Message, state: FSMContext):
    data = await state.get_data()
    debt_id = data.get("current_debt_id")
    if not debt_id:
        await message.answer("Ошибка: долг не выбран.")
        return

    result = await DebtService.close_debt(debt_id)
    if result["success"]:
        await message.answer("✅ Долг закрыт!", reply_markup=debts_menu)
    else:
        await message.answer(f"⚠️ {result['error']}", reply_markup=debts_menu)
    await state.clear()

# === Удалить долг ===
@router.message(F.text == "❌ Удалить")
async def delete_debt(message: Message, state: FSMContext):
    data = await state.get_data()
    debt_id = data.get("current_debt_id")
    if not debt_id:
        await message.answer("Ошибка: долг не выбран.")
        return

    result = await DebtService.delete_debt(debt_id)
    if result["success"]:
        await message.answer("🗑️ Долг удалён!", reply_markup=debts_menu)
    else:
        await message.answer(f"⚠️ {result['error']}", reply_markup=debts_menu)
    await state.clear()

@router.message(F.text == "📋 Назад к списку")
async def back_to_debt_list(message: Message, state: FSMContext):
    await show_debts_list(message, state)  # вызываем функцию из list.py
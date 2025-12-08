# bot/handlers/bills/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime
import re

from bot.states.bill_states import BillStates
from bot.keyboards.bills import bills_cancel, link_debt_keyboard, bills_menu
from services.bill_service import BillService
from services.debt_service import DebtService
from bot.logger import logger

router = Router()

# --- Описание ---
@router.message(F.text == "➕ Добавить счёт")
async def start_add_bill(message: Message, state: FSMContext):
    await state.set_state(BillStates.waiting_for_description)
    await message.answer("Введите название счёта (например: Ипотека за декабрь):", reply_markup=bills_cancel)

@router.message(BillStates.waiting_for_description)
async def bill_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return
    await state.update_data(description=message.text)
    await state.set_state(BillStates.waiting_for_amount)
    await message.answer("Введите сумму счёта (в рублях):", reply_markup=bills_cancel)

# --- Сумма ---
@router.message(BillStates.waiting_for_amount)
async def bill_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля.")
            return
    except ValueError:
        await message.answer("Введите корректную сумму.")
        return
    await state.update_data(amount=amount)
    await state.set_state(BillStates.waiting_for_due_date)
    await message.answer("Введите дату оплаты (ДД.ММ.ГГГГ):", reply_markup=bills_cancel)

# --- Дата ---
@router.message(BillStates.waiting_for_due_date)
async def bill_due_date(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", message.text.strip())
    if not match:
        await message.answer("Неверный формат. Введите ДД.ММ.ГГГГ:")
        return
    try:
        day, month, year = map(int, match.groups())
        due_date = datetime(year, month, day).date()
        if due_date <= datetime.now().date():
            await message.answer("Дата должна быть в будущем.")
            return
    except ValueError:
        await message.answer("Некорректная дата.")
        return

    await state.update_data(due_date=due_date)

    # Переходим к выбору привязки
    await state.set_state(BillStates.waiting_for_debt_link)
    await message.answer("Хотите привязать счёт к долгу?", reply_markup=link_debt_keyboard)

# --- Привязка к долгу ---
@router.message(BillStates.waiting_for_debt_link)
async def bill_debt_link_choice(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    if message.text == "🚫 Не привязывать":
        # Сохраняем без долга
        await _save_bill(message, state, debt_id=None)
        return

    if message.text == "🔗 Привязать к долгу":
        # Показываем список долгов
        debts = await DebtService.get_active_debts(message.from_user.id)
        if not debts:
            await message.answer("У вас нет активных долгов для привязки.", reply_markup=bills_menu)
            await state.clear()
            return

        text = "Выберите долг для привязки:\n\n"
        debt_options = {}
        for d in debts:
            label = f"{d.id}. {d.description} ({d.remaining_amount:,.2f} руб.)"
            text += label + "\n"
            debt_options[label] = d.id

        await state.update_data(debt_options=debt_options)
        await state.set_state(BillStates.waiting_for_debt_link)
        await message.answer(text, reply_markup=bills_cancel)
        return

    # Если пользователь ввёл ID вручную
    data = await state.get_data()
    debt_options = data.get("debt_options", {})
    if message.text in debt_options:
        debt_id = debt_options[message.text]
        await _save_bill(message, state, debt_id=debt_id)
    else:
        await message.answer("Выберите долг из списка или нажмите 'Не привязывать'.")

# --- Сохранение ---
async def _save_bill(message: Message, state: FSMContext, debt_id: int = None):
    data = await state.get_data()
    result = await BillService.add_bill(
        telegram_id=message.from_user.id,
        description=data["description"],
        amount=data["amount"],
        due_date=data["due_date"],
        debt_id=debt_id
    )

    if result["success"]:
        await message.answer("✅ Счёт успешно добавлен!", reply_markup=bills_menu)
    else:
        logger.error(f"Ошибка при добавлении счёта: {result['error']}")
        await message.answer("Произошла ошибка.", reply_markup=bills_menu)
    await state.clear()

async def _cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление счёта отменено.", reply_markup=bills_menu)
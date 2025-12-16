# bot/handlers/debts/edit.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re
from datetime import datetime

from bot.keyboards.debts import debts_cancel
from bot.services.debt_service import DebtService
from bot.logger import logger
from bot.keyboards.debts import debts_menu

router = Router()

class DebtEditStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_due_date = State()
    waiting_for_category = State()
    waiting_for_note = State()

# Запуск редактирования
@router.message(F.text == "✏️ Редактировать")
async def start_edit_debt(message: Message, state: FSMContext):
    data = await state.get_data()
    debt_id = data.get("current_debt_id")
    if not debt_id:
        await message.answer("Ошибка: долг не выбран.")
        return

    debt = await DebtService.get_debt_by_id(debt_id)
    await state.update_data(original_debt=debt)
    await state.set_state(DebtEditStates.waiting_for_description)
    await message.answer(
        f"Текущее название: {debt.description}\nВведите новое название (или отправьте '-' чтобы оставить):",
        reply_markup=debts_cancel
    )

# --- Описание ---
@router.message(DebtEditStates.waiting_for_description)
async def edit_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel_edit(message, state)
        return

    data = await state.get_data()
    debt = data["original_debt"]
    new_desc = message.text if message.text != "-" else debt.description
    await state.update_data(description=new_desc)
    await state.set_state(DebtEditStates.waiting_for_amount)
    await message.answer(
        f"Текущая сумма: {debt.total_amount:,.2f} руб.\nВведите новую сумму (или '-'):",
        reply_markup=debts_cancel
    )

# --- Сумма ---
@router.message(DebtEditStates.waiting_for_amount)
async def edit_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel_edit(message, state)
        return

    data = await state.get_data()
    debt = data["original_debt"]
    if message.text == "-":
        new_amount = debt.total_amount
    else:
        try:
            new_amount = float(message.text.replace(',', '.'))
            if new_amount <= 0:
                await message.answer("Сумма должна быть больше нуля.")
                return
        except ValueError:
            await message.answer("Введите корректную сумму или '-'.")
            return

    await state.update_data(amount=new_amount)
    await state.set_state(DebtEditStates.waiting_for_due_date)
    await message.answer(
        f"Текущая дата: {debt.due_date.strftime('%d.%m.%Y')}\nВведите новую дату (ДД.ММ.ГГГГ) или '-':",
        reply_markup=debts_cancel
    )

# --- Дата ---
@router.message(DebtEditStates.waiting_for_due_date)
async def edit_due_date(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel_edit(message, state)
        return

    data = await state.get_data()
    debt = data["original_debt"]
    if message.text == "-":
        new_date = debt.due_date
    else:
        match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", message.text.strip())
        if not match:
            await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ или '-'.")
            return
        try:
            day, month, year = map(int, match.groups())
            new_date = datetime(year, month, day).date()
            if new_date <= datetime.now().date():
                await message.answer("Дата должна быть в будущем.")
                return
        except ValueError:
            await message.answer("Некорректная дата.")
            return

    await state.update_data(due_date=new_date)
    await state.set_state(DebtEditStates.waiting_for_category)
    await message.answer(
        f"Текущая категория: {debt.category}\nВведите новую категорию или выберите:",
        reply_markup=_get_category_keyboard()
    )

# --- Категория и сохранение ---
@router.message(DebtEditStates.waiting_for_category)
async def edit_category(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel_edit(message, state)
        return

    valid_cats = ["Кредит", "Долг другу", "Рассрочка", "Ипотека", "Техника", "Другое"]
    if message.text not in valid_cats:
        await message.answer("Выберите категорию из списка.", reply_markup=_get_category_keyboard())
        return

    await state.update_data(category=message.text)

    if message.text == "Другое":
        await state.set_state(DebtEditStates.waiting_for_note)
        debt = (await state.get_data())["original_debt"]
        await message.answer(
            f"Текущее примечание: {debt.note or '—'}\nВведите новое примечание (или '-'):",
            reply_markup=debts_cancel
        )
    else:
        await _save_edit(message, state, note=None)

@router.message(DebtEditStates.waiting_for_note)
async def edit_note(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel_edit(message, state)
        return

    note = None if message.text == "-" else message.text
    await _save_edit(message, state, note=note)

# --- Сохранение ---
async def _save_edit(message: Message, state: FSMContext, note: str = None):
    data = await state.get_data()
    debt_id = data["original_debt"].id

    result = await DebtService.update_debt(
        debt_id=debt_id,
        description=data["description"],
        total_amount=data["amount"],
        due_date=data["due_date"],
        category=data["category"],
        note=note
    )

    if result["success"]:
        await message.answer("✅ Долг обновлён!", reply_markup=debts_menu)
    else:
        logger.error(f"Ошибка редактирования: {result['error']}")
        await message.answer("Произошла ошибка при обновлении.", reply_markup=debts_menu)
    await state.clear()

async def _cancel_edit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Редактирование отменено.", reply_markup=debts_menu)

def _get_category_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Кредит"), KeyboardButton(text="Долг другу")],
            [KeyboardButton(text="Рассрочка"), KeyboardButton(text="Ипотека")],
            [KeyboardButton(text="Техника"), KeyboardButton(text="Другое")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
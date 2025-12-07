# bot/handlers/debts/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states.debt_states import DebtStates
from bot.keyboards.debts import debts_cancel, debts_menu
from bot.services.debt_service import DebtService
from datetime import datetime, timedelta
import re
from bot.states.debt_states import DebtStates
from bot.keyboards.debts import (
    debts_cancel,
    due_date_keyboard,
    category_keyboard,
    debts_menu
)
from bot.services.debt_service import DebtService
from bot.logger import logger

router = Router()

@router.message(F.text == "➕ Добавить долг")
async def start_add_debt(message: Message, state: FSMContext):
    await state.set_state(DebtStates.waiting_for_description)
    await message.answer("Введите название долга (например: Ипотека):", reply_markup=debts_cancel)

@router.message(DebtStates.waiting_for_description)
async def debt_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return
    await state.update_data(description=message.text)
    await state.set_state(DebtStates.waiting_for_amount)
    await message.answer("Введите сумму долга (в рублях):", reply_markup=debts_cancel)

# ---- Сумма ----
@router.message(DebtStates.waiting_for_amount)
async def debt_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return
    await state.update_data(amount=amount)
    await state.set_state(DebtStates.waiting_for_due_date)
    await message.answer("Выберите дату погашения:", reply_markup=due_date_keyboard)

# ---- Дата погашения ----
@router.message(DebtStates.waiting_for_due_date)
async def debt_due_date(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    now = datetime.now().date()

    if message.text == "📅 Через неделю":
        due_date = now + timedelta(weeks=1)
    elif message.text == "📅 Через месяц":
        due_date = now + timedelta(days=30)
    elif message.text == "📅 Через 3 месяца":
        due_date = now + timedelta(days=90)
    elif message.text == "📅 Через полгода":
        due_date = now + timedelta(days=180)
    elif message.text == "✏️ Ввести вручную":
        await message.answer("Введите дату в формате ДД.ММ.ГГГГ (например: 14.12.2025):")
        return
    else:
        # Пытаемся распознать вручную введённую дату
        match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", message.text.strip())
        if not match:
            await message.answer("Неверный формат даты. Введите ДД.ММ.ГГГГ или выберите вариант ниже:", reply_markup=due_date_keyboard)
            return
        try:
            day, month, year = map(int, match.groups())
            due_date = datetime(year, month, day).date()
            if due_date <= now:
                await message.answer("Дата погашения должна быть в будущем. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("Некорректная дата. Попробуйте снова:")
            return

    await state.update_data(due_date=due_date)
    await state.set_state(DebtStates.waiting_for_category)
    await message.answer("Выберите категорию долга:", reply_markup=category_keyboard)

# ---- Категория ----
@router.message(DebtStates.waiting_for_category)
async def debt_category(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    valid_categories = {
        "🏦 Кредит": "Кредит",
        "👤 Долг другу": "Долг другу",
        "🛒 Рассрочка": "Рассрочка",
        "🏠 Ипотека": "Ипотека",
        "📱 Техника": "Техника",
        "📝 Другое": "Другое"
    }

    if message.text not in valid_categories:
        await message.answer("Пожалуйста, выберите категорию из списка:", reply_markup=category_keyboard)
        return

    category = valid_categories[message.text]
    await state.update_data(category=category)

    if category == "Другое":
        await state.set_state(DebtStates.waiting_for_note)
        await message.answer("Введите примечание к долгу:")
    else:
        await _save_debt(message, state, note=None)

# ---- Примечание (если категория 'Другое') ----
@router.message(DebtStates.waiting_for_note)
async def debt_note(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return
    await _save_debt(message, state, note=message.text)

# ---- Сохранение ----
async def _save_debt(message: Message, state: FSMContext, note: str = None):
    data = await state.get_data()
    result = await DebtService.add_debt(
        telegram_id=message.from_user.id,
        description=data["description"],
        total_amount=data["amount"],
        due_date=data["due_date"],
        category=data["category"],
        note=note
    )

    if result["success"]:
        debt = result["debt"]
        response = (
            "✅ Долг успешно добавлен!\n\n"
            f"🏦 Название: {debt.description}\n"
            f"💰 Сумма: {debt.total_amount:,.2f} руб.\n"
            f"📅 Дата погашения: {debt.due_date.strftime('%d.%m.%Y')}\n"
            f"🏷️ Категория: {debt.category}\n"
            f"📊 Остаток: {debt.remaining_amount:,.2f} руб.\n\n"
            f"ID записи: {debt.id}"
        )
        await message.answer(response, reply_markup=debts_menu)
    else:
        logger.error(f"Ошибка при добавлении долга: {result['error']}")
        await message.answer("Произошла ошибка при добавлении долга.", reply_markup=debts_menu)

    await state.clear()

# ---- Отмена ----
async def _cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление долга отменено.", reply_markup=debts_menu)
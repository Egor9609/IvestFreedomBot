# bot/handlers/bills/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import re

from bot.states.bill_states import BillStates
from bot.keyboards.bills import bills_cancel, link_debt_keyboard, bills_menu, due_date_keyboard
from bot.services.bill_service import BillService
from bot.services.debt_service import DebtService
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

    now = datetime.now().date()

    if message.text == "📅 Через неделю":
        due_date = now + timedelta(weeks=1)
    elif message.text == "📅 Через месяц":
        due_date = now + timedelta(days=30)
    elif message.text == "📅 Через 3 месяца":
        due_date = now + timedelta(days=90)
    elif message.text == "📅 Через полгода":
        due_date = now + timedelta(days=180)
    else:
        # Ручной ввод
        match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", message.text.strip())
        if not match:
            await message.answer(
                "📅 Введите дату оплаты счёта (в формате ДД.ММ.ГГГГ),\n"
                "или выберите один из вариантов:",
                reply_markup=due_date_keyboard
            )
            return
        try:
            day, month, year = map(int, match.groups())
            due_date = datetime(year, month, day).date()
            if due_date <= now:
                await message.answer("Дата должна быть в будущем.")
                return
        except ValueError:
            await message.answer("Некорректная дата. Попробуйте снова.", reply_markup=due_date_keyboard)
            return

    await state.update_data(due_date=due_date)
    await state.set_state(BillStates.waiting_for_debt_link)
    await message.answer("Хотите привязать счёт к долгу?", reply_markup=link_debt_keyboard)

# --- Привязка к долгу ---
router.message(BillStates.waiting_for_debt_link)
async def bill_debt_link_choice(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    if message.text == "🚫 Не привязывать":
        await _save_bill(message, state, debt_id=None)
        return

    # Иначе: пользователь выбрал долг из кнопок
    data = await state.get_data()
    if "debt_map" not in data:
        # Первая загрузка — покажем кнопки
        debts = await DebtService.get_active_debts(message.from_user.id)
        if not debts:
            await message.answer("Нет активных долгов.", reply_markup=bills_menu)
            await state.clear()
            return
        debt_map = {
            f"🔗 {d.id}. {d.description} ({d.remaining_amount:,.2f} руб.)": d.id
            for d in debts
        }
        await state.update_data(debt_map=debt_map)
        keyboard = build_debt_selection_keyboard_for_bills(debts)
        await message.answer("Выберите долг для привязки:", reply_markup=keyboard)
        return

    # Повторный вызов — обработка выбора
    debt_id = data["debt_map"].get(message.text)
    if debt_id:
        await _save_bill(message, state, debt_id=debt_id)
    else:
        await message.answer("Выберите долг из списка.")

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

#Добавим функцию для кнопок долгов
def build_debt_selection_keyboard_for_bills(debts):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    buttons = []
    for d in debts:
        label = f"🔗 {d.id}. {d.description} ({d.remaining_amount:,.2f} руб.)"
        buttons.append([KeyboardButton(text=label)])
    buttons.append([KeyboardButton(text="🚫 Не привязывать")])
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
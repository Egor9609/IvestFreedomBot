# bot/handlers/bills/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, date
import re

from bot.states.bill_states import BillStates
from bot.keyboards.bills import bills_cancel, link_debt_keyboard, bills_menu, due_date_keyboard
from bot.keyboards.bills import schedule_selection_keyboard, payment_frequency_keyboard
from bot.services.bill_service import BillService
from bot.services.debt_service import DebtService
from bot.logger import logger

router = Router()

FREQUENCY_MAP = {
    "📆 Каждую неделю": ("weeks", 1),
    "📆 Каждые 2 недели": ("weeks", 2),
    "📆 Каждый месяц": ("months", 1),
    "📆 Квартал (3 мес)": ("months", 3),
    "📆 Полгода": ("months", 6),
    "📆 Год": ("months", 12),
}

# --- Описание ---
@router.message(F.text == "➕ Добавить счёт")
async def start_add_bill(message: Message, state: FSMContext):
    await state.set_state(BillStates.waiting_for_debt_link)
    await message.answer("Хотите привязать счёт к долгу?", reply_markup=link_debt_keyboard)

# Остальной код: если "Да" — показываем долги → просим ввести кол-во месяцев → вызываем create_recurring_bill_from_debt
# Если "Нет" — идём по старому сценарию (ввод описания, суммы, даты)

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
    await message.answer("📅 Введите дату оплаты счёта (в формате ДД.ММ.ГГГГ),\n"
                "или выберите один из вариантов::", reply_markup=due_date_keyboard)

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
@router.message(BillStates.waiting_for_debt_link)
async def bill_debt_link_choice(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    if message.text == "🚫 Не привязывать":
        # Перейти к обычному сценарию: ввод описания → суммы → даты
        await state.set_state(BillStates.waiting_for_description)
        await message.answer("Введите название счёта (например: Ипотека за декабрь):", reply_markup=bills_cancel)
        return

    if message.text == "🔗 Привязать к долгу":
        debts = await DebtService.get_active_debts(message.from_user.id)
        if not debts:
            await message.answer("Нет активных долгов для привязки.", reply_markup=bills_menu)
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

    # Обработка выбора конкретного долга
    data = await state.get_data()
    debt_id = data["debt_map"].get(message.text)
    if not debt_id:
        await message.answer("Используйте кнопки.")
        return

    # Получаем долг
    debt = await DebtService.get_debt_by_id(debt_id)
    await state.update_data(
        linked_debt_id=debt_id,
        debt_description=debt.description,
        debt_remaining=debt.remaining_amount,
        debt_due_date=debt.due_date
    )

    # ← вместо "на сколько месяцев" — выбор режима
    await state.set_state(BillStates.waiting_for_schedule_choice)
    await message.answer(
        f"Долг: {debt.description}\nОстаток: {debt.remaining_amount:,.2f} руб.\n\n"
        "Выберите способ настройки графика:",
        reply_markup=schedule_selection_keyboard
    )

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

@router.message(BillStates.waiting_for_schedule_choice)
async def bill_schedule_choice(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    data = await state.get_data()
    due_date = data["debt_due_date"]
    today = date.today()

    if message.text == "📅 До конца погашения":
        if due_date <= today:
            await message.answer("Дата погашения уже наступила.")
            await state.clear()
            return

        # Рассчитываем ежемесячные платежи до даты
        months = max(1, (due_date.year - today.year) * 12 + (due_date.month - today.month))
        if months <= 0:
            months = 1

        # Создаём счёт
        result = await BillService.create_recurring_bill_from_debt(
            telegram_id=message.from_user.id,
            debt_id=data["linked_debt_id"],
            installments=months
        )
        await _handle_bill_result(message, result, data["debt_description"], months)
        await state.clear()

    elif message.text == "⚙️ Настроить график вручную":
        await state.set_state(BillStates.waiting_for_frequency)
        await message.answer("Выберите периодичность платежей:", reply_markup=payment_frequency_keyboard)

@router.message(BillStates.waiting_for_frequency)
async def bill_frequency_choice(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    if message.text not in FREQUENCY_MAP:
        await message.answer("Выберите из кнопок.")
        return

    freq_type, freq_value = FREQUENCY_MAP[message.text]
    await state.update_data(frequency_type=freq_type, frequency_value=freq_value)

    await state.set_state(BillStates.waiting_for_installments)
    await message.answer("Введите количество платежей (минимум 1):", reply_markup=bills_cancel)

@router.message(BillStates.waiting_for_installments)
async def bill_installments(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    try:
        installments = int(message.text)
        if installments < 1:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число ≥ 1.")
        return

    data = await state.get_data()
    freq_type = data["frequency_type"]
    freq_value = data["frequency_value"]

    # Вызываем обновлённый сервис
    result = await BillService.create_recurring_bill_from_debt(
        telegram_id=message.from_user.id,
        debt_id=data["linked_debt_id"],
        installments=installments,
        recurrence_type=freq_type,
        recurrence_value=freq_value
    )

    desc = f"{installments} платежей"
    if freq_type == "weeks":
        desc += f" каждые {freq_value} нед."
    else:
        desc += f" каждые {freq_value} мес."

    await _handle_bill_result(message, result, data["debt_description"], installments, desc)
    await state.clear()

async def _handle_bill_result(message: Message, result: dict, description: str, installments: int, custom_desc: str = None):
    if result["success"]:
        amount = result.get("amount_per_payment", 0)
        text = f"✅ Счёт создан!\n\n🧾 {description}\n"
        if custom_desc:
            text += f"📆 {custom_desc}\n"
        text += f"💵 Платёж: {amount:,.2f} руб.\n"
        text += f"🔢 Всего платежей: {installments}"
        await message.answer(text, reply_markup=bills_menu)
    else:
        logger.error(f"Ошибка: {result['error']}")
        await message.answer("Ошибка при создании счёта.", reply_markup=bills_menu)
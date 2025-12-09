# bot/handlers/bills/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, date
import re

from bot.states.bill_states import BillStates
from bot.keyboards.bills import bills_cancel, link_debt_keyboard, bills_menu, due_date_keyboard
from bot.keyboards.bills import months_selection_keyboard
from bot.services.bill_service import BillService
from bot.services.debt_service import DebtService
from bot.logger import logger

router = Router()

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
    debt_map = data.get("debt_map", {})
    debt_id = debt_map.get(message.text)

    if not debt_id:
        await message.answer("Пожалуйста, используйте кнопки.")
        return

    # Получаем долг
    debt = await DebtService.get_debt_by_id(debt_id)
    if not debt:
        await message.answer("Ошибка: долг не найден.", reply_markup=bills_menu)
        await state.clear()
        return

    # Спрашиваем: на сколько месяцев разбить?
    await state.update_data(
        linked_debt_id=debt_id,
        debt_description=debt.description,
        debt_remaining=debt.remaining_amount,
        debt_due_date = debt.due_date
    )
    await state.set_state(BillStates.waiting_for_months)
    await message.answer(
        f"Долг: {debt.description}\nОстаток: {debt.remaining_amount:,.2f} руб.\n\n"
        "На сколько месяцев разбить выплату?",
        reply_markup=months_selection_keyboard
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

@router.message(BillStates.waiting_for_months)
async def bill_months(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    data = await state.get_data()
    debt_id = data["linked_debt_id"]
    debt_description = data["debt_description"]
    debt_remaining = data["debt_remaining"]
    debt_due_date = data["debt_due_date"]  # ← нужно сохранить при выборе долга!

    months = None

    if message.text == "📅 До конца погашения долга":
        # Рассчитываем кол-во полных месяцев до даты погашения
        today = date.today()
        due = debt_due_date

        if due <= today:
            await message.answer("Дата погашения долга уже наступила или сегодня.", reply_markup=bills_menu)
            await state.clear()
            return

        # Простой расчёт: разница в днях → месяцы
        months = max(1, (due - today).days // 30)
        if months == 0:
            months = 1
    else:
        # Ручной ввод
        try:
            months = int(message.text)
            if months <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "Введите целое число (например: 10) или нажмите кнопку:",
                reply_markup=months_selection_keyboard
            )
            return

    # Создаём счёт
    result = await BillService.create_recurring_bill_from_debt(
        telegram_id=message.from_user.id,
        debt_id=debt_id,
        months=months
    )

    if result["success"]:
        await message.answer(
            f"✅ Автоматический счёт создан!\n\n"
            f"🧾 {debt_description}\n"
            f"💵 Ежемесячный платёж: {debt_remaining / months:,.2f} руб.\n"
            f"📅 Первый платёж: через 1 месяц\n"
            f"📆 Всего платежей: {months}",
            reply_markup=bills_menu
        )
    else:
        logger.error(f"Ошибка создания счёта: {result['error']}")
        await message.answer("Произошла ошибка при создании счёта.", reply_markup=bills_menu)

    await state.clear()


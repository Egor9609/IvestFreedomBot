# bot/handlers/debts/payments.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.debts import cancel_keyboard, debts_menu
from bot.services.debt_service import DebtService
from bot.logger import logger

router = Router()

class PaymentStates(StatesGroup):
    selecting_debt = State()
    entering_amount = State()

@router.message(F.text == "💳 Внести платёж")
async def start_payment(message: Message, state: FSMContext):
    debts_with_status = await DebtService.get_debts_with_status(message.from_user.id)
    if not debts_with_status:
        await message.answer("У вас нет активных долгов для оплаты.", reply_markup=debts_menu)
        return

    # Сохраняем список долгов в состоянии (для последующего сопоставления)
    debt_map = {
        f"{d['debt'].id} — {d['debt'].remaining_amount:,.2f} руб. (до {d['debt'].due_date.strftime('%d.%m.%Y')})": d['debt'].id
        for d in debts_with_status
    }
    # Добавляем эмодзи
    debt_map_full = {}
    for d in debts_with_status:
        base_label = f"{d['debt'].id} — {d['debt'].remaining_amount:,.2f} руб. (до {d['debt'].due_date.strftime('%d.%m.%Y')})"
        if d["is_overdue"]:
            label = "⚠️ " + base_label
        elif d["is_urgent"]:
            label = "🔥 " + base_label
        else:
            label = base_label
        debt_map_full[label] = d['debt'].id

    keyboard = build_debt_selection_keyboard(debts_with_status)
    await state.update_data(debt_id_map=debt_map_full)
    await state.set_state(PaymentStates.selecting_debt)
    await message.answer("💵 Выберите долг для оплаты:", reply_markup=keyboard)

@router.message(PaymentStates.selecting_debt)
async def select_debt_for_payment(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=debts_menu)
        return

    data = await state.get_data()
    debt_id_map = data.get("debt_id_map", {})

    if message.text not in debt_id_map:
        await message.answer("Пожалуйста, выберите долг из списка ниже:", reply_markup=build_debt_selection_keyboard([]))
        return

    debt_id = debt_id_map[message.text]
    debt = await DebtService.get_debt_by_id(debt_id)
    if not debt:
        await message.answer("Ошибка: долг не найден.", reply_markup=debts_menu)
        await state.clear()
        return

    await state.update_data(selected_debt_id=debt_id, debt_description=debt.description, remaining=debt.remaining_amount)
    await state.set_state(PaymentStates.entering_amount)
    await message.answer(
        f"💵 Внесение платежа\n\n"
        f"🏦 Долг: {debt.description}\n"
        f"💰 Остаток: {debt.remaining_amount:,.2f} руб.\n\n"
        f"Введите сумму платежа:",
        reply_markup=cancel_keyboard
    )

@router.message(PaymentStates.entering_amount)
async def enter_payment_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=debts_menu)
        return

    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля.")
            return
    except ValueError:
        await message.answer("Введите корректную сумму.")
        return

    data = await state.get_data()
    remaining = data["remaining"]
    if amount > remaining:
        await message.answer(f"Сумма не может превышать остаток ({remaining:,.2f} руб.). Попробуйте снова:")
        return

    debt_id = data["selected_debt_id"]
    result = await DebtService.record_payment(message.from_user.id, debt_id, amount)

    if result["success"]:
        debt = result["debt"]
        response = (
            "✅ Платёж успешно внесён!\n\n"
            f"🏦 Долг: {debt.description}\n"
            f"💵 Сумма: {amount:,.2f} руб.\n"
            f"💰 Новый остаток: {debt.remaining_amount:,.2f} руб."
        )
        await message.answer(response, reply_markup=debts_menu)
    else:
        logger.error(f"Ошибка оплаты: {result['error']}")
        await message.answer("Произошла ошибка при внесении платежа.", reply_markup=debts_menu)

    await state.clear()

def build_debt_selection_keyboard(debts_with_status):
    """Создаёт клавиатуру с кнопками долгов."""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    buttons = []
    for item in debts_with_status:
        d = item["debt"]
        # Формат: "ID — Остаток (до ДД.ММ.ГГГГ)"
        label = f"{d.id} — {d.remaining_amount:,.2f} руб. (до {d.due_date.strftime('%d.%m.%Y')})"
        if item["is_overdue"]:
            label = "⚠️ " + label
        elif item["is_urgent"]:
            label = "🔥 " + label
        buttons.append([KeyboardButton(text=label)])

    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
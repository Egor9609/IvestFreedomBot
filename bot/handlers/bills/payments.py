# bot/handlers/bills/payments.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.bills import bills_menu, bills_cancel
from bot.services.bill_service import BillService
from bot.logger import logger

router = Router()

class BillPaymentStates(StatesGroup):
    selecting_bill = State()

def build_bill_selection_keyboard(bills):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    buttons = []
    for b in bills:
        label = f"{b.id}. {b.description} — {b.amount:,.2f} руб. (до {b.due_date.strftime('%d.%m.%Y')})"
        buttons.append([KeyboardButton(text=label)])
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.message(F.text == "💳 Оплатить счёт")
async def start_pay_bill(message: Message, state: FSMContext):
    bills = await BillService.get_active_bills(message.from_user.id)
    if not bills:
        await message.answer("У вас нет неоплаченных счетов.", reply_markup=bills_menu)
        return

    keyboard = build_bill_selection_keyboard(bills)
    bill_map = {f"{b.id}. {b.description} — {b.amount:,.2f} руб. (до {b.due_date.strftime('%d.%m.%Y')})": b.id for b in bills}
    await state.update_data(bill_map=bill_map)
    await state.set_state(BillPaymentStates.selecting_bill)
    await message.answer("Выберите счёт для оплаты:", reply_markup=keyboard)

@router.message(BillPaymentStates.selecting_bill)
async def confirm_pay_bill(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Оплата отменена.", reply_markup=bills_menu)
        return

    data = await state.get_data()
    bill_id = data["bill_map"].get(message.text)
    if not bill_id:
        await message.answer("Выберите счёт из списка.")
        return

    result = await BillService.pay_bill(message.from_user.id, bill_id)
    if result["success"]:
        bill = result["bill"]
        response = (
            "✅ Счёт оплачен!\n\n"
            f"🧾 Счёт: {bill.description}\n"
            f"💵 Сумма: {bill.amount:,.2f} руб.\n"
            f"📅 Дата оплаты: {bill.paid_at.strftime('%d.%m.%Y %H:%M')}"
        )
        # Если был привязан долг — он уменьшился
        await message.answer(response, reply_markup=bills_menu)
    else:
        logger.error(f"Ошибка оплаты счёта: {result['error']}")
        await message.answer("Произошла ошибка при оплате.", reply_markup=bills_menu)

    await state.clear()
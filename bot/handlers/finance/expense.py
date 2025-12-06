# bot/handlers/finance/expense.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.finance_states import ExpenseStates
from bot.keyboards.finance import expense_cancel_keyboard, expense_description_keyboard
from bot.keyboards.base import main_menu
from services.finance_service import FinanceService
from bot.logger import logger

router = Router()

@router.message(Command("expense"))
async def cmd_expense_start(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.waiting_for_amount)
    await message.answer("Введите сумму расхода:", reply_markup=expense_cancel_keyboard)


@router.message(ExpenseStates.waiting_for_amount)
async def cmd_expense_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Добавление расхода отменено.", reply_markup=main_menu)
        return

    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (например: 850.99):")
        return

    await state.update_data(amount=amount)
    await state.set_state(ExpenseStates.waiting_for_description)
    await message.answer("Введите описание расхода (либо нажмите “Пропустить”):", reply_markup=expense_description_keyboard)


@router.message(ExpenseStates.waiting_for_description)
async def cmd_expense_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Добавление расхода отменено.", reply_markup=main_menu)
        return

    description = None if message.text == "Пропустить" else message.text
    data = await state.get_data()
    amount = data.get("amount")

    if amount is None:
        await state.clear()
        await message.answer("Произошла ошибка: сумма не сохранена. Начните заново.", reply_markup=main_menu)
        return

    # Вызываем сервис
    try:
        result = await FinanceService.add_expense(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            amount=amount,
            description=description
        )
    except Exception as e:
        logger.error(f"Исключение при вызове FinanceService.add_expense: {e}", exc_info=True)
        await state.clear()
        await message.answer("Произошла внутренняя ошибка. Попробуйте позже.", reply_markup=main_menu)
        return

    if result.get("success"):
        desc_text = description if description else "—"
        response = (
            "✅ Расход добавлен!\n"
            f"Сумма: {amount:.2f} руб.\n"
            f"Примечание: {desc_text}"
        )
        await message.answer(response, reply_markup=main_menu)
    else:
        error_msg = result.get("error", "Неизвестная ошибка")
        logger.error(f"Ошибка при добавлении расхода: {error_msg}")
        await message.answer("Не удалось добавить расход. Попробуйте позже.", reply_markup=main_menu)

    await state.clear()
# bot/handlers/debts/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states.debt_states import DebtStates
from bot.keyboards.debts import debts_cancel, debts_menu
from services.debt_service import DebtService
from bot.logger import logger

router = Router()

@router.message(F.text == "➕ Добавить долг")
async def start_add_debt(message: Message, state: FSMContext):
    await state.set_state(DebtStates.waiting_for_description)
    await message.answer("Введите описание долга (например: Ипотека):", reply_markup=debts_cancel)

@router.message(DebtStates.waiting_for_description)
async def debt_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Добавление долга отменено.", reply_markup=debts_menu)
        return

    await state.update_data(description=message.text)
    await state.set_state(DebtStates.waiting_for_amount)
    await message.answer("Введите сумму долга (в рублях):", reply_markup=debts_cancel)

@router.message(DebtStates.waiting_for_amount)
async def debt_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Добавление долга отменено.", reply_markup=debts_menu)
        return

    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return

    data = await state.get_data()
    description = data["description"]

    result = await DebtService.add_debt(
        telegram_id=message.from_user.id,
        description=description,
        total_amount=amount
    )

    if result["success"]:
        await message.answer("✅ Долг успешно добавлен!", reply_markup=debts_menu)
    else:
        logger.error(f"Ошибка при добавлении долга: {result['error']}")
        await message.answer("Произошла ошибка при добавлении долга.", reply_markup=debts_menu)

    await state.clear()
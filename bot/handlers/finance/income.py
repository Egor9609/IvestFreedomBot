# bot/handlers/finance/income.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.finance_states import IncomeStates
from bot.keyboards.finance import description_keyboard, cancel_keyboard
from bot.keyboards.base import main_menu  # Главное меню
from bot.logger import logger
from database.repository import UserRepository, TransactionRepository
from database.session import get_session
from bot.services.finance_service import FinanceService

router = Router()

print("✅ bot/handlers/finance/income.py Загружается")

@router.message(lambda m: m.text == "💰 Доходы")
async def handle_income_button(message: Message, state: FSMContext):
    # Просто вызываем команду /income
    await cmd_income_start(message, state)

@router.message(Command("income"))
async def cmd_income_start(message: Message, state: FSMContext):
    await state.set_state(IncomeStates.waiting_for_amount)
    await message.answer("Введите сумму дохода:", reply_markup=cancel_keyboard)


@router.message(IncomeStates.waiting_for_amount)
async def cmd_income_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Добавление дохода отменено.", reply_markup=main_menu)
        return

    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (например: 1500.50):")
        return

    await state.update_data(amount=amount)
    await state.set_state(IncomeStates.waiting_for_description)
    await message.answer("Введите описание дохода (либо нажмите “Пропустить”):", reply_markup=description_keyboard)


@router.message(IncomeStates.waiting_for_description)
async def cmd_income_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Добавление дохода отменено.", reply_markup=main_menu)
        return

    description = None if message.text == "Пропустить" else message.text

    data = await state.get_data()
    amount = data.get("amount")

    # Вызываем сервис — вся логика здесь
    result = await FinanceService.add_income(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        amount=amount,
        description=description
    )

    if result["success"]:
        desc_text = description if description else "—"
        response = (
            "✅ Доход добавлен!\n"
            f"Сумма: {amount:.2f} руб.\n"
            f"Примечание: {desc_text}"
        )
        await message.answer(response, reply_markup=main_menu)
    else:
        logger.error(f"Ошибка при добавлении дохода: {result['error']}")
        await message.answer("Произошла ошибка при добавлении дохода. Попробуйте позже.", reply_markup=main_menu)

    await state.clear()

print("✅ bot/handlers/finance/income.py ЗАГРУЖЕН")
# bot/handlers/finance/income.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.finance_states import IncomeStates
from bot.keyboards.finance import cancel_keyboard
from bot.logger import logger
from database.repository import UserRepository, TransactionRepository
from database.session import get_session

router = Router()

print("✅ bot/handlers/finance/income.py ЗАГРУЖЕН")

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
        await message.answer("Добавление дохода отменено.")
        return

    try:
        amount = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return

    await state.update_data(amount=amount)
    await state.set_state(IncomeStates.waiting_for_description)
    await message.answer("Введите описание дохода (или нажмите 'Пропустить'):")


@router.message(IncomeStates.waiting_for_description)
async def cmd_income_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Добавление дохода отменено.")
        return

    if message.text == "Пропустить":
        description = None
    else:
        description = message.text

    data = await state.get_data()
    amount = data.get("amount")

    # Получаем сессию и работаем с БД
    async for session in get_session():
        try:
            user_repo = UserRepository(session)
            transaction_repo = TransactionRepository(session)

            user = await user_repo.get_or_create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )

            await transaction_repo.add_transaction(
                user_id=user.id,
                type="income",
                amount=amount,
                description=description
            )

            await session.commit()
            await message.answer(f"Доход в размере {amount} добавлен!")

        except Exception as e:
            logger.error(f"Ошибка при добавлении дохода: {e}", exc_info=True)
            await message.answer("Произошла ошибка при добавлении дохода. Попробуйте позже.")

        finally:
            await state.clear()
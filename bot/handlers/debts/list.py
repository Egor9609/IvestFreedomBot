# bot/handlers/debts/list.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date

from services.debt_service import DebtService
from bot.keyboards.debts import debts_menu
from bot.states.debt_states import DebtListStates

router = Router()

@router.message(F.text == "📋 Список долгов")
async def show_debts_list(message: Message, state: FSMContext):
    debts = await DebtService.get_active_debts(message.from_user.id)

    if not debts:
        await message.answer("У вас нет активных долгов.", reply_markup=debts_menu)
        return

    # === Часть 1: Текстовый отчёт (как раньше) ===
    text = "📋 Ваши активные долги:\n\n"
    total_remaining = 0

    for i, d in enumerate(debts, 1):
        days_left = (d.due_date - date.today()).days

        # Статус
        if days_left <= 7:
            status = "🔥 Срочно"
        else:
            status = "✅ В порядке"

        # Категория
        category = d.category if d.category != "Другое" else "Другое"
        if category == "Другое" and d.note:
            category = f"Другое ({d.note})"

        text += (
            f"{i}. {d.description}\n"
            f"   💰 {d.remaining_amount:,.2f} / {d.total_amount:,.2f} руб.\n"
            f"   📅 {d.due_date.strftime('%d.%m.%Y')}\n"
            f"   🏷️ {category}\n"
            f"   ⏱️ {status} ({days_left} дней)\n\n"
        )
        total_remaining += d.remaining_amount

    text += f"📊 Итого к погашению: {total_remaining:,.2f} руб."

    # === Часть 2: Кнопки долгов (как сейчас) ===
    buttons = []
    debt_map = {}

    for d in debts:
        note_part = f" — ({d.note})" if d.note else ""
        label = f"{d.id} — {d.category}{note_part} — {d.remaining_amount:,.2f} руб."
        buttons.append([KeyboardButton(text=label)])
        debt_map[label] = d.id

    # Кнопка "Назад"
    buttons.append([KeyboardButton(text="📋 Назад к меню долгов")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    # Сохраняем маппинг для FSM
    await state.update_data(debt_map=debt_map)
    await state.set_state(DebtListStates.selecting_debt)

    # Отправляем сначала текст, потом кнопки
    await message.answer(text, reply_markup=debts_menu)  # текст без кнопок
    await message.answer("Выберите долг для управления:", reply_markup=keyboard)
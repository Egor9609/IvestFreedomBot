# bot/states/debt_states.py

from aiogram.fsm.state import State, StatesGroup

class DebtStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_due_date = State()
    waiting_for_category = State()
    waiting_for_note = State()

class DebtListStates(StatesGroup):
    selecting_debt = State()

class DebtDetailStates(StatesGroup):
    viewing_detail = State()
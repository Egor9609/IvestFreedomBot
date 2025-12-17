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
    selecting_debt = State()
    viewing_detail = State()
    confirming_close = State()
    confirming_delete = State()
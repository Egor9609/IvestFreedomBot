# bot/states/finance_states.py
from aiogram.fsm.state import State, StatesGroup

class IncomeStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()

class ExpenseStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()
# bot/states/bill_states.py

from aiogram.fsm.state import State, StatesGroup

class BillStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_due_date = State()
    waiting_for_debt_link = State()  # ← выбор долга для привязки
    waiting_for_months = State()
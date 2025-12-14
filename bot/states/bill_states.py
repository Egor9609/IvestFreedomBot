# bot/states/bill_states.py

from aiogram.fsm.state import State, StatesGroup

class BillStates(StatesGroup):
    waiting_for_description = State() # 4. Название (если не привязан)
    waiting_for_amount = State() # 5. Сумма
    waiting_for_due_date = State() # 6. Дата
    waiting_for_debt_link = State()  # 1. Привязывать или нет?
    waiting_for_debt_selection = State()  # 2. Выбор конкретного долга
    waiting_for_months = State()    # 3. Сколько месяцев?
    waiting_for_schedule_choice = State()
    waiting_for_frequency = State()
    waiting_for_installments = State()
    waiting_for_months = State()
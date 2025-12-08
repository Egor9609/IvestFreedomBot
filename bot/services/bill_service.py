# services/bill_service.py
from datetime import datetime

from bot.database.repository import UserRepository, BillRepository, DebtRepository
from bot.database.session import get_session

class BillService:
    @staticmethod
    async def add_bill(telegram_id: int, description: str, amount: float, due_date: datetime, debt_id: int = None):
        async for session in get_session():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}

            # Проверяем долг
            if debt_id:
                debt_repo = DebtRepository(session)
                debt = await debt_repo.get_debt_by_id(debt_id)
                if not debt or debt.user_id != user.id:
                    return {"success": False, "error": "Долг не найден или не принадлежит вам"}

            bill_repo = BillRepository(session)
            # Передаём telegram_id напрямую, НЕ через user
            bill = await bill_repo.add_bill(
                user_id=user.id,
                telegram_id=telegram_id,  # ← явно передаём
                description=description,
                amount=amount,
                due_date=due_date,
                debt_id=debt_id
            )
            return {"success": True, "bill_id": bill.id}

    @staticmethod
    async def get_active_bills(telegram_id: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return []
            bill_repo = BillRepository(session)
            return await bill_repo.get_active_bills_by_user(user.id)

    @staticmethod
    async def pay_bill(telegram_id: int, bill_id: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}

            bill_repo = BillRepository(session)
            bill = await bill_repo.get_bill_by_id(bill_id)
            if not bill or bill.user_id != user.id:
                return {"success": False, "error": "Счёт не найден"}

            paid_bill = await bill_repo.pay_bill(bill_id)
            if paid_bill:
                return {"success": True, "bill": paid_bill}
            else:
                return {"success": False, "error": "Счёт уже оплачен"}
# services/debt_service.py

from database.repository import UserRepository, DebtRepository
from database.session import get_session
from datetime import datetime

class DebtService:
    @staticmethod
    async def add_debt(
            telegram_id: int,
            description: str,
            total_amount: float,
            due_date: datetime,
            category: str,
            note: str = None
    ):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}

            debt = await debt_repo.add_debt(
                user_id=user.id,
                description=description,
                total_amount=total_amount,
                due_date=due_date,
                category=category,
                note=note
            )
            return {"success": True, "debt": debt}

    @staticmethod
    async def get_active_debts(telegram_id: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return []

            debts = await debt_repo.get_active_debts_by_user(user.id)
            return debts
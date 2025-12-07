# services/debt_service.py

from database.repository import UserRepository, DebtRepository
from database.session import get_session

class DebtService:
    @staticmethod
    async def add_debt(telegram_id: int, description: str, total_amount: float):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}

            debt = await debt_repo.add_debt(
                user_id=user.id,
                description=description,
                total_amount=total_amount
            )
            return {"success": True, "debt_id": debt.id}

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
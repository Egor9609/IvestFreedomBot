# services/debt_service.py

from bot.database.repository import UserRepository, DebtRepository
from bot.database.session import get_session
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

    @staticmethod
    async def record_payment(telegram_id: int, debt_id: int, amount: float):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}

            debt = await debt_repo.get_debt_by_id(debt_id)
            if not debt or debt.user_id != user.id:
                return {"success": False, "error": "Долг не найден"}

            updated_debt = await debt_repo.record_payment(debt_id, amount)
            if updated_debt:
                return {"success": True, "debt": updated_debt, "amount_paid": amount}
            else:
                return {"success": False, "error": "Некорректная сумма"}

    @staticmethod
    async def get_debt_statistics(telegram_id: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {}
            return await debt_repo.get_debt_statistics(user.id)

    @staticmethod
    async def get_debts_with_status(telegram_id: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return []
            return await debt_repo.get_debts_with_status(user.id)

    @staticmethod
    async def get_debt_by_id(debt_id: int):
        async for session in get_session():
            debt_repo = DebtRepository(session)
            return await debt_repo.get_debt_by_id(debt_id)
# services/finance_service.py
from typing import Optional
from bot.database.repository import UserRepository, TransactionRepository
from bot.database.session import get_session


class FinanceService:
    @staticmethod
    async def add_transaction(
        telegram_id: int,
        username: Optional[str],
        full_name: Optional[str],
        amount: float,
        transaction_type: str,  # "income" или "expense"
        description: Optional[str] = None
    ) -> dict:
        async for session in get_session():
            try:
                user_repo = UserRepository(session)
                transaction_repo = TransactionRepository(session)

                user = await user_repo.get_or_create_user(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name
                )

                await transaction_repo.add_transaction(
                    user_id=user.id,
                    type=transaction_type,
                    amount=amount,
                    description=description
                )

                await session.commit()
                return {"success": True, "user_id": user.id}

            except Exception as e:
                await session.rollback()
                return {"success": False, "error": str(e)}

    # Удобные обёртки (опционально)
    @staticmethod
    async def add_income(*args, **kwargs):
        return await FinanceService.add_transaction(*args, transaction_type="income", **kwargs)

    @staticmethod
    async def add_expense(*args, **kwargs):
        return await FinanceService.add_transaction(*args, transaction_type="expense", **kwargs)
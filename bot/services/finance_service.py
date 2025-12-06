# services/finance_service.py
from typing import Optional
from database.repository import UserRepository, TransactionRepository
from database.session import get_session


class FinanceService:
    @staticmethod
    async def add_income(
        telegram_id: int,
        username: Optional[str],
        full_name: Optional[str],
        amount: float,
        description: Optional[str] = None
    ) -> dict:
        """
        Добавляет доход пользователя в базу данных.
        Возвращает словарь с результатом: {'success': bool, 'error': str или None}
        """
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
                    type="income",
                    amount=amount,
                    description=description
                )

                await session.commit()
                return {"success": True, "user_id": user.id}

            except Exception as e:
                await session.rollback()
                return {"success": False, "error": str(e)}
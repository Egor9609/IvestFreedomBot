# services/finance_service.py
from typing import Optional
from bot.database.repository import UserRepository, TransactionRepository
from bot.database.session import get_session

from datetime import datetime, timedelta
import pytz

MSK = pytz.timezone('Europe/Moscow')

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

    @staticmethod
    async def get_balance_report(telegram_id: int, period: str) -> dict:
        """Возвращает отчёт: доходы, расходы, баланс, кол-во операций за период."""
        async for session in get_session():
            user_repo = UserRepository(session)
            trans_repo = TransactionRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"error": "Пользователь не найден"}

            transactions = await trans_repo.get_transactions_by_user_and_period(user.id, period)

            income = sum(t.amount for t in transactions if t.type == "income")
            expense = sum(t.amount for t in transactions if t.type == "expense")
            balance = income - expense
            count = len(transactions)

            # Формируем заголовок отчёта
            now = datetime.now(MSK)
            if period == "day":
                title_date = now.strftime("%d.%m.%Y")
            elif period == "week":
                start = now - timedelta(days=now.weekday())
                title_date = f"{start.strftime('%d.%m.%Y')} – {now.strftime('%d.%m.%Y')}"
            elif period == "month":
                title_date = now.strftime("%B %Y")
            elif period == "year":
                title_date = str(now.year)
            else:
                title_date = "период"

            return {
                "success": True,
                "title": title_date,
                "income": income,
                "expense": expense,
                "balance": balance,
                "count": count
            }



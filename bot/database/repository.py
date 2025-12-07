# bot/database/repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Transaction, Debt
from datetime import datetime, timedelta
import pytz

MSK = pytz.timezone('Europe/Moscow')

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, telegram_id: int, username: str = None, full_name: str = None):
        # Ищем пользователя по telegram_id
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Если нет — создаём нового
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def get_user_by_id(self, user_id: int):
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_status(self, user_id: int, is_active: bool):
        user = await self.get_user_by_id(user_id)
        if user:
            user.is_active = is_active
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def get_user_by_telegram_id(self, telegram_id: int):
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_transaction(self, user_id: int, type: str, amount: float, description: str = None, date: str = None):
        transaction = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            description=description,
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def get_transactions_by_user(self, user_id: int):
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_total_income_by_user(self, user_id: int):
        stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == "income"
        )
        result = await self.session.execute(stmt)
        total = result.scalar()
        return total or 0.0

    async def get_total_expense_by_user(self, user_id: int):
        stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense"
        )
        result = await self.session.execute(stmt)
        total = result.scalar()
        return total or 0.0

    @staticmethod
    def _get_period_bounds(period: str):
        """Возвращает (start, end) для заданного периода в MSK."""
        now = datetime.now(MSK).replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "day":
            start = now
            end = now + timedelta(days=1)
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(weeks=1)
        elif period == "month":
            start = now.replace(day=1)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        elif period == "year":
            start = now.replace(month=1, day=1)
            end = start.replace(year=now.year + 1)
        else:
            raise ValueError("Неверный период")
        return start, end

    async def get_transactions_by_user_and_period(self, user_id: int, period: str):
        start, end = self._get_period_bounds(period)  # ← вызываем через self
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date < end
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

class DebtRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_debt(
            self,
            user_id: int,
            description: str,
            total_amount: float,
            due_date: datetime,
            category: str,
            note: str = None
    ):
        debt = Debt(
            user_id=user_id,
            description=description,
            total_amount=total_amount,
            remaining_amount=total_amount,
            due_date=due_date,
            category=category,
            note=note
        )
        self.session.add(debt)
        await self.session.commit()
        await self.session.refresh(debt)
        return debt

    async def get_active_debts_by_user(self, user_id: int):
        stmt = select(Debt).where(Debt.user_id == user_id, Debt.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_debt_by_id(self, debt_id: int):
        stmt = select(Debt).where(Debt.id == debt_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
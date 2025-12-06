# database/repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Transaction


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
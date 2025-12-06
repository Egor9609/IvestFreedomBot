# test/sync_repository.py
from sqlalchemy import select
from database.models import User, Transaction


class SyncUserRepository:
    def __init__(self, session):
        self.session = session

    def get_or_create_user(self, telegram_id: int, username: str = None, full_name: str = None):
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name
            )
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

        return user

    def get_user_by_id(self, user_id: int):
        stmt = select(User).where(User.id == user_id)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def update_user_status(self, user_id: int, is_active: bool):
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = is_active
            self.session.commit()
            self.session.refresh(user)
        return user


class SyncTransactionRepository:
    def __init__(self, session):
        self.session = session

    def add_transaction(self, user_id: int, type: str, amount: float, description: str = None, date: str = None):
        transaction = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            description=description,
            date=date
        )
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def get_transactions_by_user(self, user_id: int):
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        result = self.session.execute(stmt)
        return result.scalars().all()

    def get_total_income_by_user(self, user_id: int):
        stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == "income"
        )
        result = self.session.execute(stmt)
        total = result.scalar()
        return total or 0.0

    def get_total_expense_by_user(self, user_id: int):
        stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense"
        )
        result = self.session.execute(stmt)
        total = result.scalar()
        return total or 0.0
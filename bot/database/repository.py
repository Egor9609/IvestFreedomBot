# bot/database/repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Transaction, Debt
from datetime import datetime, timedelta, date
import pytz
from decimal import Decimal

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
            total_amount=Decimal(str(total_amount)),
            remaining_amount=Decimal(str(total_amount)),
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

    async def record_payment(self, debt_id: int, amount: float):
        debt = await self.get_debt_by_id(debt_id)
        if not debt:
            return None
        if amount <= 0:
            return None

        # Приводим amount к Decimal
        payment_amount = Decimal(str(amount))  # ВАЖНО: через строку, чтобы избежать float-ошибок

        if payment_amount > debt.remaining_amount:
            payment_amount = debt.remaining_amount

        debt.remaining_amount -= payment_amount

        if debt.remaining_amount <= Decimal("0"):
            debt.is_active = False
            debt.remaining_amount = Decimal("0")

        await self.session.commit()
        await self.session.refresh(debt)
        return debt

    async def get_debts_with_status(self, user_id: int):
        """Возвращает долги с флагами: is_overdue, days_left"""
        from datetime import date
        today = date.today()
        stmt = select(Debt).where(Debt.user_id == user_id, Debt.is_active == True)
        result = await self.session.execute(stmt)
        debts = result.scalars().all()

        enriched = []
        for d in debts:
            due = d.due_date
            days_left = (due - today).days
            enriched.append({
                "debt": d,
                "days_left": days_left,
                "is_overdue": days_left < 0,
                "is_urgent": days_left <= 7 and days_left >= 0
            })
        return enriched

    async def get_debt_statistics(self, user_id: int):
        stmt = select(Debt).where(Debt.user_id == user_id)
        result = await self.session.execute(stmt)
        all_debts = result.scalars().all()

        total_debts = len(all_debts)
        total_amount = sum(float(d.total_amount) for d in all_debts)
        remaining = sum(float(d.remaining_amount) for d in all_debts)
        paid = total_amount - remaining

        # Просроченные
        overdue_debts = [d for d in all_debts if d.is_active and d.due_date < date.today()]
        overdue_amount = sum(float(d.remaining_amount) for d in overdue_debts)

        # По категориям
        from collections import defaultdict
        by_category = defaultdict(lambda: {"count": 0, "total": 0.0, "paid": 0.0})
        for d in all_debts:
            cat = d.category if d.category != "Другое" else f"Другое ({d.note})" if d.note else "Другое"
            by_category[cat]["count"] += 1
            by_category[cat]["total"] += float(d.total_amount)
            by_category[cat]["paid"] += float(d.total_amount - d.remaining_amount)

        # Ближайшие сроки (активные, отсортированы по дате)
        active_debts = [d for d in all_debts if d.is_active]
        nearest = sorted(active_debts, key=lambda x: x.due_date)[:5]

        return {
            "total_debts": total_debts,
            "total_amount": total_amount,
            "remaining": remaining,
            "paid": paid,
            "overdue_count": len(overdue_debts),
            "overdue_amount": overdue_amount,
            "by_category": dict(by_category),
            "nearest": nearest
        }
# bot/database/models.py
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Numeric, Boolean, ForeignKey, Date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import pytz

# Определяем московский часовой пояс
MSK = pytz.timezone('Europe/Moscow')

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(MSK)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String, nullable=False)  # 'income' или 'expense'
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(MSK)
    )

class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)  # Например: "Ипотека"
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # Полная сумма долга
    remaining_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # Остаток
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)  # только дата
    category: Mapped[str] = mapped_column(String, nullable=False)  # "Кредит", "Другое" и т.д.
    note: Mapped[str] = mapped_column(String, nullable=True)  # для "Другое"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(MSK))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Активен ли долг (не погашен полностью)
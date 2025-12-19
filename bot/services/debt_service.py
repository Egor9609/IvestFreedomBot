# services/debt_service.py

from bot.database.repository import UserRepository, DebtRepository, DebtPaymentRepository
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

    @staticmethod
    async def get_unlinked_active_debts(telegram_id: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return []
            return await debt_repo.get_unlinked_active_debts_by_user(user.id)

    @staticmethod
    async def update_debt(debt_id: int, description: str, total_amount: float, due_date, category: str,
                          note: str = None):
        async for session in get_session():
            debt_repo = DebtRepository(session)
            debt = await debt_repo.get_debt_by_id(debt_id)
            if not debt:
                return {"success": False, "error": "Долг не найден"}

            # Обновляем поля
            debt.description = description
            debt.total_amount = total_amount
            debt.due_date = due_date
            debt.category = category
            debt.note = note

            # Если новая сумма < старого остатка — корректируем остаток
            if total_amount < debt.remaining_amount:
                debt.remaining_amount = total_amount

            await session.commit()
            return {"success": True}

    @staticmethod
    async def close_debt(debt_id: int):
        """Помечает долг как закрытый (остаток = 0)."""
        async for session in get_session():
            debt_repo = DebtRepository(session)
            debt = await debt_repo.get_debt_by_id(debt_id)
            if not debt or not debt.is_active:
                return {"success": False, "error": "Долг не найден или уже закрыт"}

            debt.remaining_amount = 0
            debt.is_active = False
            await session.commit()
            return {"success": True}

    @staticmethod
    async def delete_debt(debt_id: int):
        """Удаляет долг, только если по нему не было платежей."""
        async for session in get_session():
            # Проверяем, были ли платежи
            payment_repo = DebtPaymentRepository(session)
            payments = await payment_repo.get_payments_by_debt(debt_id)
            if payments:
                return {"success": False, "error": "Нельзя удалить долг, по которому уже были платежи"}

            debt_repo = DebtRepository(session)
            debt = await debt_repo.get_debt_by_id(debt_id)
            if not debt:
                return {"success": False, "error": "Долг не найден"}

            await session.delete(debt)
            await session.commit()
            return {"success": True}

    @staticmethod
    async def create_debt_with_schedule(telegram_id: int, description: str, total_amount: float, due_date,
                                        category: str, note: str, months: int):
        async for session in get_session():
            user_repo = UserRepository(session)
            debt_repo = DebtRepository(session)
            schedule_repo = PaymentScheduleRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            debt = Debt(
                user_id=user.id,
                telegram_id=telegram_id,
                description=description,
                total_amount=total_amount,
                remaining_amount=total_amount,
                due_date=due_date,
                category=category,
                note=note
            )
            session.add(debt)
            await session.flush()  # получаем debt.id

            # Сразу создаём график
            await schedule_repo.create_schedule(debt.id, months)

            await session.commit()
            await session.refresh(debt)
            return {"success": True, "debt_id": debt.id}
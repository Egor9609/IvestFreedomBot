# test/test_repository.py
import pytest
from test.sync_repository import SyncUserRepository, SyncTransactionRepository


def test_user_repository(session):
    user_repo = SyncUserRepository(session)

    # Тестируем создание пользователя
    user = user_repo.get_or_create_user(telegram_id=12345, username="test_user", full_name="Test User")
    assert user.telegram_id == 12345
    assert user.username == "test_user"

    # Повторный вызов — должен вернуть того же пользователя
    same_user = user_repo.get_or_create_user(telegram_id=12345)
    assert same_user.id == user.id


def test_transaction_repository(session):
    user_repo = SyncUserRepository(session)
    transaction_repo = SyncTransactionRepository(session)

    # Сначала создадим пользователя
    user = user_repo.get_or_create_user(telegram_id=12345, username="test_user", full_name="Test User")

    # Добавим транзакцию
    transaction = transaction_repo.add_transaction(
        user_id=user.id,
        type="income",
        amount=1000.0,
        description="Тестовый доход"
    )

    assert transaction.user_id == user.id
    assert transaction.type == "income"
    assert transaction.amount == 1000.0
    assert transaction.description == "Тестовый доход"
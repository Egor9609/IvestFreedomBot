# test/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base


# Используем отдельную тестовую БД в памяти
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL)
sync_session = sessionmaker(bind=engine)


@pytest.fixture
def session():
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)

    # Создаём сессию
    session = sync_session()
    yield session

    # Закрываем сессию и удаляем таблицы
    session.close()
    Base.metadata.drop_all(bind=engine)
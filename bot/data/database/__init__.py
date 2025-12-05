# database/__init__.py
from .models import Base
from .session import engine

async def create_db_and_tables():
    async with engine.begin() as conn:
        # Создаём таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)
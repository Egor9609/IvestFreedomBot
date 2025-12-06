# database/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from bot.config import DATABASE_PATH

# Создаём папку, если её нет
db_dir = os.path.dirname(DATABASE_PATH)
os.makedirs(db_dir, exist_ok=True)

# Асинхронный движок
engine = create_async_engine(f"sqlite+aiosqlite:///{DATABASE_PATH}")

# Асинхронная фабрика сессий
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
# bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scheduler.jobs import send_bill_reminders

from bot.config import BOT_TOKEN
from bot.handlers import register_all_routers
from bot.logger import logger  # подключим, чтобы инициализировать
from bot.database import create_db_and_tables

# Включаем логирование (опционально)
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Планировщик
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_bill_reminders, "cron", hour=9, minute=0, args=[bot])
    scheduler.start()

        # Создаём таблицы при запуске
    await create_db_and_tables()
    register_all_routers(dp)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")

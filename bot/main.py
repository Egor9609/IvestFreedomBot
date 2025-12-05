# bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import register_all_routers
from bot.logger import logger  # подключим, чтобы инициализировать

# Включаем логирование (опционально)
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

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
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
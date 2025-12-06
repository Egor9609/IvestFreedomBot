# bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не указан в .env файле!")

# Указываем путь относительно корня проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # IvestFreedomBot/
DATABASE_PATH = os.path.join(PROJECT_ROOT, os.getenv("DB_PATH", "data/database/finance.db"))
ADMINS_FILE = os.path.join(PROJECT_ROOT, os.getenv("ADMINS_FILE", "data/admins.txt"))
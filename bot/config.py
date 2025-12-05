# bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не указан в .env файле!")

DATABASE_PATH = os.getenv("DB_PATH", "data/database/finance.db")
ADMINS_FILE = os.getenv("ADMINS_FILE", "data/admins.txt")
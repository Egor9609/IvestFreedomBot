# bot/handlers/__init__.py
from aiogram import Dispatcher, Router
from .base import router as base_router
from .finance import setup_finance_routers

def register_all_routers(dp: Dispatcher):
    dp.include_router(base_router)
    dp.include_router(setup_finance_routers())
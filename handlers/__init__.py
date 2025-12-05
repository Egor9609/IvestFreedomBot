# bot/handlers/__init__.py
from aiogram import Dispatcher
from .base import router as base_router

def register_all_routers(dp: Dispatcher):
    dp.include_router(base_router)
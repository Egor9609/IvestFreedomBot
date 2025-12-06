# bot/handlers/finance/__init__.py
from aiogram import Router
from .income import router as income_router


def setup_finance_routers() -> Router:
    router = Router()
    router.include_router(income_router)
    return router
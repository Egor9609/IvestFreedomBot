# bot/handlers/finance/__init__.py
from aiogram import Router
from .income import router as income_router
from .expense import router as expense_router


def setup_finance_routers() -> Router:
    router = Router()
    router.include_router(income_router)
    router.include_router(expense_router)
    return router
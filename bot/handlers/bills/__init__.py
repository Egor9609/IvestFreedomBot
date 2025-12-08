# bot/handlers/bills/__init__.py

from aiogram import Router
from .add import router as add_router
from .payments import router as payments_router

def setup_bills_routers() -> Router:
    router = Router()
    router.include_router(add_router)
    router.include_router(payments_router)
    return router
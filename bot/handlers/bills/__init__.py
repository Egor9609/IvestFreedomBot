# bot/handlers/bills/__init__.py

from aiogram import Router
from .add import router as add_router

def setup_bills_routers() -> Router:
    router = Router()
    router.include_router(add_router)
    return router
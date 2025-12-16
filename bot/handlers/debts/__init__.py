# bot/handlers/debts/__init__.py

from aiogram import Router
from .add import router as add_router
from .list import router as list_router
from .detail import router as detail_router
from .payments import router as payments_router
from .reports import router as reports_router
from .edit import router as edit_router

def setup_debts_routers() -> Router:
    router = Router()
    router.include_router(add_router)
    router.include_router(list_router)
    router.include_router(detail_router)
    router.include_router(payments_router)
    router.include_router(reports_router)
    router.include_router(edit_router)
    return router
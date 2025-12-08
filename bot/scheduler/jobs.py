# scheduler/jobs.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date, timedelta
from aiogram import Bot
from services.bill_service import BillService

async def send_bill_reminders(bot: Bot):
    """Отправляет напоминания за 1 день до срока счёта."""
    from database.repository import BillRepository
    from database.session import get_session

    tomorrow = date.today() + timedelta(days=1)

    async for session in get_session():
        # Получаем все неоплаченные счета на завтра
        stmt = select(Bill).where(
            Bill.due_date == tomorrow,
            Bill.is_paid == False
        )
        result = await session.execute(stmt)
        bills = result.scalars().all()

        for bill in bills:
            try:
                await bot.send_message(
                    chat_id=bill.user_id,  # ⚠️ нужно хранить telegram_id, а не user_id!
                    text=(
                        "🔔 Напоминание!\n\n"
                        f"Завтра нужно оплатить счёт:\n"
                        f"🧾 {bill.description}\n"
                        f"💵 {bill.amount:,.2f} руб.\n"
                        f"📅 {bill.due_date.strftime('%d.%m.%Y')}"
                    )
                )
            except Exception as e:
                logger.error(f"Не удалось отправить напоминание пользователю {bill.user_id}: {e}")
# services/export_service.py
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import pytz
from sqlalchemy import select

from bot.database.repository import UserRepository, TransactionRepository, DebtRepository
from bot.database.session import get_session
from bot.database.models import Debt


MSK = pytz.timezone('Europe/Moscow')

class ExportService:
    @staticmethod
    async def export_transactions_to_excel(telegram_id: int, period: str) -> tuple[BytesIO, str] | None:
        async for session in get_session():
            user_repo = UserRepository(session)
            trans_repo = TransactionRepository(session)
            debt_repo = DebtRepository(session)  # ✅ Теперь импортировано

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return None

            # === Сбор транзакций ===
            transactions = await trans_repo.get_transactions_by_user_and_period(user.id, period)
            df = pd.DataFrame()
            total_income = total_expense = 0.0

            if transactions:
                data = []
                for t in transactions:
                    amount = float(t.amount)
                    if t.type == "income":
                        total_income += amount
                    else:
                        total_expense += amount
                    data.append({
                        "Дата": t.date.strftime("%d.%m.%Y %H:%M"),
                        "Тип": "Доход" if t.type == "income" else "Расход",
                        "Сумма (руб.)": amount,
                        "Описание": t.description or "—"
                    })
                df = pd.DataFrame(data)
                df = df.sort_values("Дата", ascending=False)

            # === Итоги в виде отдельных строк ===
            if not df.empty:
                separator = pd.DataFrame([{"Дата": "", "Тип": "", "Сумма (руб.)": "", "Описание": ""}])
                summary = pd.DataFrame([
                    {"Дата": "Итоги:", "Тип": "Доходы", "Сумма (руб.)": total_income, "Описание": "руб."},
                    {"Дата": "", "Тип": "Расходы", "Сумма (руб.)": total_expense, "Описание": "руб."},
                    {"Дата": "", "Тип": "Баланс", "Сумма (руб.)": total_income - total_expense, "Описание": "руб."},
                ])
                final_df = pd.concat([df, separator, summary], ignore_index=True)
            else:
                final_df = pd.DataFrame(columns=["Дата", "Тип", "Сумма (руб.)", "Описание"])

            # === Сбор долгов ===
            debts = await debt_repo.get_active_debts_by_user(user.id)
            debts_df = pd.DataFrame()
            total_remaining = total_paid = 0.0

            if debts:
                debt_data = []
                for d in debts:
                    paid = float(d.total_amount - d.remaining_amount)
                    total_remaining += float(d.remaining_amount)
                    total_paid += paid
                    debt_data.append({
                        "ID": d.id,
                        "Название": d.description,
                        "Категория": d.category,
                        "Примечание": d.note or "—",
                        "Полная сумма (руб.)": float(d.total_amount),
                        "Остаток (руб.)": float(d.remaining_amount),
                        "Дата погашения": d.due_date.strftime("%d.%m.%Y")
                    })
                debts_df = pd.DataFrame(debt_data)

            # === Имя файла ===
            now = datetime.now(MSK)
            if period == "day":
                date_str = now.strftime("%d.%m.%Y")
                filename = f"Отчёт_за_{date_str}.xlsx"
            elif period == "week":
                start = now - timedelta(days=now.weekday())
                date_str = f"{start.strftime('%d.%m.%Y')}-{now.strftime('%d.%m.%Y')}"
                filename = f"Отчёт_за_неделю_{date_str}.xlsx"
            elif period == "month":
                date_str = now.strftime("%m.%Y")
                filename = f"Отчёт_за_месяц_{date_str}.xlsx"
            elif period == "year":
                date_str = str(now.year)
                filename = f"Отчёт_за_год_{date_str}.xlsx"
            else:
                filename = "Отчёт.xlsx"

            # === Запись в Excel ===
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Лист: Транзакции
                if not final_df.empty:
                    final_df.to_excel(writer, index=False, sheet_name="Транзакции")
                    worksheet = writer.sheets["Транзакции"]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

                # Лист: Долги
                if not debts_df.empty:
                    debts_df.to_excel(writer, index=False, sheet_name="Долги")
                    worksheet = writer.sheets["Долги"]
                    last_row = len(debts_df) + 2
                    worksheet.cell(row=last_row, column=4, value="ИТОГО:")
                    worksheet.cell(row=last_row, column=5, value="Остаток по долгам:")
                    worksheet.cell(row=last_row, column=6, value=total_remaining)
                    worksheet.cell(row=last_row + 1, column=5, value="Уже выплачено:")
                    worksheet.cell(row=last_row + 1, column=6, value=total_paid)

                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

            output.seek(0)
            return output, filename

    async def get_active_debts_by_user(self, user_id: int):
        stmt = select(Debt).where(Debt.user_id == user_id, Debt.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()
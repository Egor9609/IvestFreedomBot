# services/export_service.py
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import pytz
from database.repository import TransactionRepository
from database.session import get_session

MSK = pytz.timezone('Europe/Moscow')

class ExportService:
    @staticmethod
    async def export_transactions_to_excel(telegram_id: int, period: str) -> tuple[BytesIO, str] | None:
        """
        Экспортирует транзакции за период в Excel.
        Возвращает (BytesIO, filename) или None.
        """
        async for session in get_session():
            from database.repository import UserRepository
            user_repo = UserRepository(session)
            trans_repo = TransactionRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return None

            transactions = await trans_repo.get_transactions_by_user_and_period(user.id, period)
            if not transactions:
                return None

            # Определяем дату для имени файла
            now = datetime.now(MSK)
            if period == "day":
                date_str = now.strftime("%d.%m.%Y")
                filename = f"Отчёт_{date_str}.xlsx"
            elif period == "week":
                start = now - timedelta(days=now.weekday())
                date_str = f"{start.strftime('%d.%m.%Y')}-{now.strftime('%d.%m.%Y')}"
                filename = f"Отчёт_неделя_{date_str}.xlsx"
            elif period == "month":
                date_str = now.strftime("%m.%Y")
                filename = f"Отчёт_месяц_{date_str}.xlsx"
            elif period == "year":
                date_str = str(now.year)
                filename = f"Отчёт_год_{date_str}.xlsx"
            else:
                filename = "Отчёт.xlsx"

            # Подготавливаем данные
            data = []
            total_income = 0.0
            total_expense = 0.0

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

            # Создаём DataFrame
            df = pd.DataFrame(data)
            df = df.sort_values("Дата", ascending=False)

            # Добавляем итоговую строку
            balance = total_income - total_expense
            total_row = {
                "Дата": "ИТОГО:",
                "Тип": "",
                "Сумма (руб.)": "",
                "Описание": ""
            }
            df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

            # Форматируем итоговую строку отдельно
            df.loc[df.index[-1], "Тип"] = f"Доходы: {total_income:,.2f} руб."
            df.loc[df.index[-1], "Сумма (руб.)"] = f"Расходы: {total_expense:,.2f} руб."
            df.loc[df.index[-1], "Описание"] = f"Баланс: {balance:,.2f} руб."

            # Сохраняем в Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Операции")

                # Автоширина колонок
                worksheet = writer.sheets["Операции"]
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
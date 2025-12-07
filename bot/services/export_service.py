# services/export_service.py
import pandas as pd
from io import BytesIO
from database.repository import TransactionRepository
from database.session import get_session


class ExportService:
    @staticmethod
    async def export_transactions_to_excel(telegram_id: int, period: str) -> BytesIO | None:
        """
        Экспортирует транзакции пользователя за период в Excel.
        Возвращает BytesIO-объект с файлом или None, если нет данных.
        """
        async for session in get_session():
            # Получаем пользователя и его транзакции за период
            from database.repository import UserRepository
            user_repo = UserRepository(session)
            trans_repo = TransactionRepository(session)

            user = await user_repo.get_user_by_telegram_id(telegram_id)
            if not user:
                return None

            transactions = await trans_repo.get_transactions_by_user_and_period(user.id, period)

            if not transactions:
                return None

            # Преобразуем в список словарей
            data = []
            for t in transactions:
                data.append({
                    "Дата": t.date.strftime("%d.%m.%Y %H:%M"),
                    "Тип": "Доход" if t.type == "income" else "Расход",
                    "Сумма (руб.)": t.amount,
                    "Описание": t.description or "—"
                })

            # Создаём DataFrame
            df = pd.DataFrame(data)

            # Сортируем по дате (новые — сверху)
            df = df.sort_values("Дата", ascending=False)

            # Сохраняем в BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Операции")

                # Автоматическая ширина колонок
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
            return output
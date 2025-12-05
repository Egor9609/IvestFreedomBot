# bot/logger.py
import logging
import os

# Убедимся, что папка logs существует
log_dir = "data/logs"
os.makedirs(log_dir, exist_ok=True)

# Настраиваем логгер
logger = logging.getLogger("finbot")
logger.setLevel(logging.DEBUG)  # Принимаем всё

# Формат сообщения
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Обработчик для записи в файл
error_handler = logging.FileHandler(os.path.join(log_dir, "errors.log"), encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# Обработчик для вывода в консоль (добавь это)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Только ошибки в консоль
console_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
if not logger.handlers:  # избегаем дублирования
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)  # Добавляем консольный обработчик

# Чтобы логи не дублировались в консоли
logger.propagate = False
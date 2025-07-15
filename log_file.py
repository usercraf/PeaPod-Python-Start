import logging
from logging.handlers import RotatingFileHandler

# === Основна конфігурація логування ===
logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)  # Міняй на INFO / WARNING / ERROR, якщо треба

# === Формат для всіх хендлерів ===
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# === Хендлер у файл з обмеженням розміру (лог-обертання) ===
LOG_PATH = "/home/orangepi/PeaPod-Python-Start/bot.log"
file_handler = RotatingFileHandler(
    LOG_PATH,
    maxBytes=1_000_000,
    backupCount=5,
    encoding="utf-8"
)

file_handler.setFormatter(formatter)

# === Хендлер для консолі ===
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# === Уникаємо дублювання хендлерів при імпорті ===
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

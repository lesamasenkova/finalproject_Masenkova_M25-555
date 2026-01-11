"""Настройка системы логирования."""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_level=logging.INFO):
    """
    Настроить систему логирования.
    
    Args:
        log_level: Уровень логирования (по умолчанию INFO)
    """
    # Создаем директорию для логов
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Формат логов
    log_format = "%(levelname)s %(asctime)s %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"

    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "actions.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Консольный обработчик (только для WARNING и выше)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# Инициализируем логирование при импорте
setup_logging()


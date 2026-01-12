"""Точка входа в приложение."""

import logging
from pathlib import Path

from valutatrade_hub.cli.interface import CLI


def setup_directories():
    """Создать необходимые директории."""
    for directory in ["data", "logs"]:
        Path(directory).mkdir(exist_ok=True)


def setup_logging():
    """Настройка логирования."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/actions.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main():
    """Главная функция приложения."""
    setup_directories()
    setup_logging()
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()


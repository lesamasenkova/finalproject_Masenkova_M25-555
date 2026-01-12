"""Конфигурация Parser Service."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()


@dataclass
class ParserConfig:
    """Конфигурация для Parser Service."""

    # API ключи (из переменных окружения)
    EXCHANGERATE_API_KEY: str = field(
        default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY", "")
    )

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Базовая валюта
    BASE_CURRENCY: str = "USD"

    # Фиатные валюты для отслеживания
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB", "JPY", "CNY")

    # Криптовалюты для отслеживания
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL", "USDT", "BNB", "XRP")

    # Маппинг кодов криптовалют на ID CoinGecko
    CRYPTO_ID_MAP: dict = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "USDT": "tether",
            "BNB": "binancecoin",
            "XRP": "ripple",
        }
    )

    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10

    def validate(self):
        """Проверить корректность конфигурации."""
        if not self.EXCHANGERATE_API_KEY:
            raise ValueError(
                "EXCHANGERATE_API_KEY не установлен! "
                "Добавьте его в файл .env или установите переменную окружения."
            )


"""Клиенты для работы с внешними API."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig

logger = logging.getLogger(__name__)


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов."""

    def __init__(self, config: ParserConfig):
        """
        Инициализация клиента.
        
        Args:
            config: Конфигурация парсера
        """
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получить курсы валют.
        
        Returns:
            Словарь {пара: курс}, например {"BTC_USD": 59337.21}
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API."""

    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы криптовалют от CoinGecko."""
        logger.info("Fetching crypto rates from CoinGecko...")

        # Формируем список ID валют
        crypto_ids = [
            self.config.CRYPTO_ID_MAP[code]
            for code in self.config.CRYPTO_CURRENCIES
            if code in self.config.CRYPTO_ID_MAP
        ]

        # Формируем URL
        url = self.config.COINGECKO_URL
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": "usd",
        }

        try:
            response = requests.get(
                url, params=params, timeout=self.config.REQUEST_TIMEOUT
            )

            # Проверяем статус
            if response.status_code == 429:
                raise ApiRequestError("Rate limit exceeded (429 Too Many Requests)")
            
            response.raise_for_status()

            data = response.json()

            # Преобразуем в стандартный формат
            rates = {}
            for code, coin_id in self.config.CRYPTO_ID_MAP.items():
                if coin_id in data and "usd" in data[coin_id]:
                    rate = data[coin_id]["usd"]
                    rates[f"{code}_USD"] = rate

            logger.info(f"Successfully fetched {len(rates)} crypto rates")
            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Connection error")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Request failed: {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Unexpected error: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API."""

    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы фиатных валют от ExchangeRate-API."""
        logger.info("Fetching fiat rates from ExchangeRate-API...")

        # Проверяем наличие API ключа
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("ExchangeRate-API key is not configured")

        # Формируем URL
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)

            # Проверяем статус
            if response.status_code == 429:
                raise ApiRequestError("Rate limit exceeded (429 Too Many Requests)")
            elif response.status_code == 403:
                raise ApiRequestError("Invalid API key (403 Forbidden)")
            
            response.raise_for_status()

            data = response.json()

            # Проверяем результат
            if data.get("result") != "success":
                raise ApiRequestError(f"API returned error: {data.get('error-type', 'unknown')}")

            # Извлекаем курсы
            raw_rates = data.get("rates", {})

            # Преобразуем в стандартный формат
            rates = {}
            for code in self.config.FIAT_CURRENCIES:
                if code in raw_rates:
                    # Для фиатных валют курс указывается как валюта->USD
                    # Но API возвращает USD->валюта, поэтому инвертируем
                    rate = 1.0 / raw_rates[code] if raw_rates[code] != 0 else 0
                    rates[f"{code}_USD"] = rate

            logger.info(f"Successfully fetched {len(rates)} fiat rates")
            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Connection error")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Request failed: {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Unexpected error: {str(e)}")


"""Клиенты для работы с внешними API."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

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

    def _fetch_with_retry(
        self, url: str, params: dict, max_retries: int = 3
    ) -> Optional[dict]:
        """
        Запрос с повторными попытками при rate limit.

        Args:
            url: URL для запроса
            params: Параметры запроса
            max_retries: Максимальное количество попыток

        Returns:
            Ответ API в формате JSON или None

        Raises:
            ApiRequestError: При ошибке после всех попыток
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)

                if response.status_code == 429:
                    wait_time = 2**attempt
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise ApiRequestError("Request timeout")
                logger.warning(f"Attempt {attempt + 1} timed out")

            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    raise ApiRequestError("Connection error")
                logger.warning(f"Attempt {attempt + 1} connection failed")

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise ApiRequestError(f"Request failed: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

        raise ApiRequestError("Max retries exceeded")


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
            "vs_currencies": self.config.BASE_CURRENCY.lower(), 
        }

        try:
            data = self._fetch_with_retry(url, params) 

            if data is None:
                raise ApiRequestError("Failed to fetch data from CoinGecko")

            # Преобразуем в стандартный формат
            rates = {}
            base_lower = self.config.BASE_CURRENCY.lower()
            for code, coin_id in self.config.CRYPTO_ID_MAP.items():
                if coin_id in data and base_lower in data[coin_id]:
                    rate = data[coin_id][base_lower]
                    rates[f"{code}_{self.config.BASE_CURRENCY}"] = rate

            logger.info(f"Successfully fetched {len(rates)} crypto rates")
            return rates

        except ApiRequestError:
            raise
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
                raise ApiRequestError(
                    f"API returned error: {data.get('error-type', 'unknown')}"
                )

            # Извлекаем курсы
            raw_rates = data.get("conversion_rates", {})

            # Преобразуем в стандартный формат
            # API возвращает USD->другая_валюта (например USD->EUR = 0.85)
            # Нам нужно EUR_USD = 1/0.85 = 1.176
            rates = {}
            for code in self.config.FIAT_CURRENCIES:
                if code == self.config.BASE_CURRENCY:
                    # Пропускаем пару USD_USD
                    continue

                if code in raw_rates and raw_rates[code] != 0:
                    # Инвертируем курс: если USD_EUR = 0.85, то EUR_USD = 1/0.85
                    rates[f"{code}_{self.config.BASE_CURRENCY}"] = 1.0 / raw_rates[code]

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


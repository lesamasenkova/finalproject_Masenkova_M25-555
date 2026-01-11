"""Иерархия валют с полиморфизмом."""

from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.exceptions import CurrencyNotFoundError, ValidationError


class Currency(ABC):
    """Абстрактный базовый класс для валюты."""

    def __init__(self, code: str, name: str):
        """
        Инициализация валюты.
        
        Args:
            code: Код валюты (ISO или тикер)
            name: Человекочитаемое название
        """
        # Валидация кода
        if not code or not isinstance(code, str):
            raise ValidationError("Код валюты должен быть непустой строкой")
        
        code = code.upper().strip()
        if len(code) < 2 or len(code) > 5:
            raise ValidationError("Код валюты должен содержать от 2 до 5 символов")
        
        if " " in code:
            raise ValidationError("Код валюты не должен содержать пробелов")
        
        # Валидация названия
        if not name or not isinstance(name, str) or not name.strip():
            raise ValidationError("Название валюты не может быть пустым")
        
        self.code = code
        self.name = name

    @abstractmethod
    def get_display_info(self) -> str:
        """Получить строковое представление для UI/логов."""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта (государственная)."""

    def __init__(self, code: str, name: str, issuing_country: str):
        """
        Инициализация фиатной валюты.
        
        Args:
            code: Код валюты
            name: Название
            issuing_country: Страна/зона эмиссии
        """
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """Получить строковое представление фиатной валюты."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(self, code: str, name: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализация криптовалюты.
        
        Args:
            code: Код валюты
            name: Название
            algorithm: Алгоритм консенсуса
            market_cap: Рыночная капитализация
        """
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """Получить строковое представление криптовалюты."""
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"


# Реестр валют
_CURRENCY_REGISTRY: Dict[str, Currency] = {
    # Фиатные валюты
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "GBP": FiatCurrency("GBP", "British Pound", "United Kingdom"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "JPY": FiatCurrency("JPY", "Japanese Yen", "Japan"),
    "CNY": FiatCurrency("CNY", "Chinese Yuan", "China"),
    
    # Криптовалюты
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.5e11),
    "USDT": CryptoCurrency("USDT", "Tether", "Omni", 8.3e10),
    "BNB": CryptoCurrency("BNB", "Binance Coin", "BFT", 7.2e10),
    "SOL": CryptoCurrency("SOL", "Solana", "PoH", 5.1e10),
    "XRP": CryptoCurrency("XRP", "Ripple", "RPCA", 2.8e10),
}


def get_currency(code: str) -> Currency:
    """
    Получить валюту по коду из реестра.
    
    Args:
        code: Код валюты
        
    Returns:
        Объект Currency
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    code = code.upper().strip()
    
    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    
    return _CURRENCY_REGISTRY[code]


def get_all_currency_codes() -> list:
    """
    Получить список всех поддерживаемых кодов валют.
    
    Returns:
        Список кодов валют
    """
    return list(_CURRENCY_REGISTRY.keys())


def is_currency_supported(code: str) -> bool:
    """
    Проверить, поддерживается ли валюта.
    
    Args:
        code: Код валюты
        
    Returns:
        True если поддерживается
    """
    return code.upper().strip() in _CURRENCY_REGISTRY


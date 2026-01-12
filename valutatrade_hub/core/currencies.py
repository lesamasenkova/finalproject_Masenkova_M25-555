"""Иерархия валют с полиморфизмом."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
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
        
        if not isinstance(code, str):
            raise ValidationError("Код валюты должен быть строкой")
        if not code.strip():
            raise ValidationError("Код валюты не может быть пустым")

        code = code.upper().strip()

        if len(code) < 2 or len(code) > 5:
            raise ValidationError("Код валюты должен содержать от 2 до 5 символов")
        if " " in code:
            raise ValidationError("Код валюты не должен содержать пробелов")

        # Валидация названия
        if not isinstance(name, str):
            raise ValidationError("Название валюты должно быть строкой")
        if not name.strip():
            raise ValidationError("Название валюты не может быть пустым")

        self.code = code
        self.name = name

    @abstractmethod
    def get_display_info(self) -> str:
        """Получить строковое представление для UI/логов."""
        pass

    def __repr__(self) -> str:  
        """Строковое представление объекта."""
        return f"{self.__class__.__name__}(code='{self.code}', name='{self.name}')"

    def __eq__(self, other) -> bool:  
        """Сравнение валют по коду."""
        if not isinstance(other, Currency):
            return False
        return self.code == other.code

    def __hash__(self) -> int:  
        """Хеш валюты."""
        return hash(self.code)


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



def _load_currency_registry() -> Dict[str, Currency]:
    """
    Загрузить реестр валют из JSON файла.

    Returns:
        Словарь {код: объект Currency}
    """
    currencies_file = Path("data/currencies.json")

    # Если файл не существует, создаем с дефолтными валютами
    if not currencies_file.exists():
        currencies_file.parent.mkdir(parents=True, exist_ok=True)

        default_data = {
            "fiat": [
                {"code": "USD", "name": "US Dollar", "issuing_country": "United States"},
                {"code": "EUR", "name": "Euro", "issuing_country": "Eurozone"},
                {"code": "GBP", "name": "British Pound", "issuing_country": "United Kingdom"},
                {"code": "RUB", "name": "Russian Ruble", "issuing_country": "Russia"},
                {"code": "JPY", "name": "Japanese Yen", "issuing_country": "Japan"},
                {"code": "CNY", "name": "Chinese Yuan", "issuing_country": "China"},
            ],
            "crypto": [
                {"code": "BTC", "name": "Bitcoin", "algorithm": "SHA-256", "market_cap": 1.12e12},
                {"code": "ETH", "name": "Ethereum", "algorithm": "Ethash", "market_cap": 4.5e11},
                {"code": "USDT", "name": "Tether", "algorithm": "Omni", "market_cap": 8.3e10},
                {"code": "BNB", "name": "Binance Coin", "algorithm": "BFT", "market_cap": 7.2e10},
                {"code": "SOL", "name": "Solana", "algorithm": "PoH", "market_cap": 5.1e10},
                {"code": "XRP", "name": "Ripple", "algorithm": "RPCA", "market_cap": 2.8e10},
            ],
        }

        with open(currencies_file, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

    # Загружаем из файла
    try:
        with open(currencies_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValidationError(f"Не удалось загрузить currencies.json: {e}")

    registry = {}

    # Загружаем фиатные валюты
    for item in data.get("fiat", []):
        try:
            currency = FiatCurrency(**item)
            if currency.code in registry:
                raise ValidationError(f"Дубликат валюты: {currency.code}")
            registry[currency.code] = currency
        except (TypeError, KeyError) as e:
            print(f"Предупреждение: пропуск некорректной фиатной валюты: {e}")

    # Загружаем криптовалюты
    for item in data.get("crypto", []):
        try:
            currency = CryptoCurrency(**item)
            if currency.code in registry:
                raise ValidationError(f"Дубликат валюты: {currency.code}")
            registry[currency.code] = currency
        except (TypeError, KeyError) as e:
            print(f"Предупреждение: пропуск некорректной криптовалюты: {e}")

    return registry


# Глобальный реестр валют
_CURRENCY_REGISTRY = _load_currency_registry()


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


def reload_currency_registry():
    """Перезагрузить реестр валют из файла."""
    global _CURRENCY_REGISTRY
    _CURRENCY_REGISTRY = _load_currency_registry()


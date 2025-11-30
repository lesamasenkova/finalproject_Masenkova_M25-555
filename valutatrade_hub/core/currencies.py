"""
Модуль определения типов валют и фабрики для их получения.
Содержит абстрактный класс Currency и его наследников (FiatCurrency, CryptoCurrency).
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict


class Currency(ABC):
    """
    Абстрактный базовый класс для всех валют.
    
    Определяет общий интерфейс и инварианты для фиатных и криптовалют.
    """
    
    def __init__(self, name: str, code: str):
        """
        Инициализация валюты.
        
        Args:
            name: Человекочитаемое имя валюты (например, "US Dollar")
            code: ISO-код или тикер (например, "USD", "BTC")
            
        Raises:
            ValueError: Если name пустое или code некорректен.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Имя валюты не может быть пустым")
        
        if not self._validate_code(code):
            raise ValueError(
                f"Код валюты должен быть 2-5 символов, верхний регистр, без пробелов. "
                f"Получено: {code}"
            )
        
        self._name = name.strip()
        self._code = code.upper().strip()
    
    @property
    def name(self) -> str:
        """Возвращает имя валюты."""
        return self._name
    
    @property
    def code(self) -> str:
        """Возвращает код валюты."""
        return self._code
    
    @staticmethod
    def _validate_code(code: str) -> bool:
        """
        Валидирует код валюты.
        
        Правила:
        - 2-5 символов
        - Только латинские буквы и цифры
        - Верхний регистр
        - Без пробелов
        """
        if not isinstance(code, str):
            return False
        
        code = code.strip()
        
        if not (2 <= len(code) <= 5):
            return False
        
        if not code.isupper():
            return False
        
        if not code.isalnum():
            return False
        
        return True
    
    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает отформатированную информацию о валюте.
        
        Для CLI и логов.
        
        Returns:
            Строка с информацией о валюте.
        """
        pass
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return f"{self.__class__.__name__}(code='{self.code}', name='{self.name}')"
    
    def __str__(self) -> str:
        """Строковое представление."""
        return f"{self.code}"
    
    def __eq__(self, other) -> bool:
        """Сравнение валют по коду."""
        if not isinstance(other, Currency):
            return False
        return self.code == other.code
    
    def __hash__(self) -> int:
        """Хеш для использования в словарях и множествах."""
        return hash(self.code)


class FiatCurrency(Currency):
    """
    Фиатная валюта (государственная, например USD, EUR, RUB).
    
    Атрибуты:
        issuing_country: Страна или организация-эмитент.
    """
    
    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.
        
        Args:
            name: Имя валюты (например, "US Dollar")
            code: ISO-код (например, "USD")
            issuing_country: Страна-эмитент (например, "United States")
        """
        super().__init__(name, code)
        
        if not issuing_country or not isinstance(issuing_country, str):
            raise ValueError("Страна-эмитент не может быть пустой")
        
        self._issuing_country = issuing_country.strip()
    
    @property
    def issuing_country(self) -> str:
        """Возвращает страну-эмитент."""
        return self._issuing_country
    
    def get_display_info(self) -> str:
        """
        Форматирует информацию о фиатной валюте.
        
        Пример вывода:
            "[FIAT] USD — US Dollar (Issuing: United States)"
        """
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return (
            f"FiatCurrency(code='{self.code}', name='{self.name}', "
            f"issuing_country='{self.issuing_country}')"
        )


class CryptoCurrency(Currency):
    """
    Криптовалюта (например BTC, ETH, SOL).
    
    Атрибуты:
        algorithm: Алгоритм консенсуса/хеширования.
        market_cap: Рыночная капитализация в USD (опционально).
    """
    
    def __init__(self, name: str, code: str, algorithm: str, market_cap: Optional[float] = None):
        """
        Инициализация криптовалюты.
        
        Args:
            name: Имя валюты (например, "Bitcoin")
            code: Тикер (например, "BTC")
            algorithm: Алгоритм (например, "SHA-256")
            market_cap: Рыночная капитализация в USD (опционально)
        """
        super().__init__(name, code)
        
        if not algorithm or not isinstance(algorithm, str):
            raise ValueError("Алгоритм не может быть пустым")
        
        self._algorithm = algorithm.strip()
        
        if market_cap is not None and market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        
        self._market_cap = market_cap
    
    @property
    def algorithm(self) -> str:
        """Возвращает алгоритм."""
        return self._algorithm
    
    @property
    def market_cap(self) -> Optional[float]:
        """Возвращает рыночную капитализацию."""
        return self._market_cap
    
    def get_display_info(self) -> str:
        """
        Форматирует информацию о криптовалюте.
        
        Примеры вывода:
            "[CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e12)"
            "[CRYPTO] ETH — Ethereum (Algo: Ethash, MCAP: 0.00)"
        """
        algo_info = f"Algo: {self.algorithm}"
        
        if self._market_cap is not None:
            if self._market_cap >= 1e12:
                mcap_str = f"{self._market_cap:.2e}"
            else:
                mcap_str = f"{self._market_cap:.2f}"
            algo_info += f", MCAP: {mcap_str}"
        
        return f"[CRYPTO] {self.code} — {self.name} ({algo_info})"
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return (
            f"CryptoCurrency(code='{self.code}', name='{self.name}', "
            f"algorithm='{self.algorithm}', market_cap={self.market_cap})"
        )


# ============= Реестр валют и фабрика =============

class CurrencyRegistry:
    """
    Реестр и фабрика для получения валют по коду.
    
    Хранит предопределённый список поддерживаемых валют и предоставляет
    методы для поиска и получения объектов валют.
    """
    
    def __init__(self):
        """Инициализация реестра с предопределёнными валютами."""
        self._currencies: Dict[str, Currency] = {}
        self._initialize_currencies()
    
    def _initialize_currencies(self) -> None:
        """Инициализирует встроенный набор валют."""
        
        # Фиатные валюты
        fiat_currencies = [
            FiatCurrency("US Dollar", "USD", "United States"),
            FiatCurrency("Euro", "EUR", "Eurozone"),
            FiatCurrency("British Pound", "GBP", "United Kingdom"),
            FiatCurrency("Russian Ruble", "RUB", "Russia"),
            FiatCurrency("Japanese Yen", "JPY", "Japan"),
            FiatCurrency("Chinese Yuan", "CNY", "China"),
            FiatCurrency("Swiss Franc", "CHF", "Switzerland"),
            FiatCurrency("Canadian Dollar", "CAD", "Canada"),
            FiatCurrency("Australian Dollar", "AUD", "Australia"),
        ]
        
        # Криптовалюты
        crypto_currencies = [
            CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
            CryptoCurrency("Ethereum", "ETH", "Ethash", 2.95e11),
            CryptoCurrency("Solana", "SOL", "Proof of Stake", 6.8e10),
            CryptoCurrency("Ripple", "XRP", "XRPL Consensus", 2.5e10),
            CryptoCurrency("Cardano", "ADA", "Ouroboros", 1.8e10),
            CryptoCurrency("Polkadot", "DOT", "Nominated Proof-of-Stake", 1.4e10),
            CryptoCurrency("Litecoin", "LTC", "Scrypt", 1.2e10),
        ]
        
        # Добавляем все валюты в реестр
        for currency in fiat_currencies + crypto_currencies:
            self._currencies[currency.code] = currency
    
    def get(self, code: str) -> Currency:
        """
        Получает объект валюты по коду.
        
        Args:
            code: Код валюты (например, "BTC", "USD")
            
        Returns:
            Объект Currency (FiatCurrency или CryptoCurrency)
            
        Raises:
            ValueError: Если код некорректен.
            CurrencyNotFoundError: Если валюта не найдена в реестре.
        """
        from valutatrade_hub.core.exceptions import CurrencyNotFoundError
        
        # Валидируем код
        if not Currency._validate_code(code):
            raise ValueError(
                f"Некорректный код валюты '{code}'. "
                f"Код должен быть 2-5 символов, верхний регистр."
            )
        
        code = code.upper().strip()
        
        if code not in self._currencies:
            raise CurrencyNotFoundError(code)
        
        return self._currencies[code]
    
    def get_all(self) -> Dict[str, Currency]:
        """Возвращает копию всех валют из реестра."""
        return self._currencies.copy()
    
    def get_all_fiat(self) -> Dict[str, FiatCurrency]:
        """Возвращает все фиатные валюты."""
        return {
            code: curr 
            for code, curr in self._currencies.items()
            if isinstance(curr, FiatCurrency)
        }
    
    def get_all_crypto(self) -> Dict[str, CryptoCurrency]:
        """Возвращает все криптовалюты."""
        return {
            code: curr 
            for code, curr in self._currencies.items()
            if isinstance(curr, CryptoCurrency)
        }
    
    def exists(self, code: str) -> bool:
        """Проверяет, существует ли валюта с данным кодом."""
        try:
            self.get(code)
            return True
        except (ValueError, Exception):
            return False
    
    def add_custom(self, currency: Currency) -> None:
        """
        Добавляет пользовательскую валюту в реестр (для расширений).
        
        Args:
            currency: Объект Currency для добавления.
        """
        if not isinstance(currency, Currency):
            raise TypeError("Аргумент должен быть объектом Currency")
        
        self._currencies[currency.code] = currency
    
    def __len__(self) -> int:
        """Возвращает количество валют в реестре."""
        return len(self._currencies)
    
    def __repr__(self) -> str:
        """Представление для отладки."""
        return f"CurrencyRegistry(currencies={len(self._currencies)})"


# Глобальный реестр валют (Singleton pattern)
_GLOBAL_REGISTRY: Optional[CurrencyRegistry] = None


def get_currency_registry() -> CurrencyRegistry:
    """
    Получает глобальный реестр валют (создаёт его при первом вызове).
    
    Returns:
        Глобальный объект CurrencyRegistry.
    """
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = CurrencyRegistry()
    return _GLOBAL_REGISTRY


def get_currency(code: str) -> Currency:
    """
    Быстрый способ получить валюту по коду.
    
    Args:
        code: Код валюты (например, "BTC")
        
    Returns:
        Объект Currency.
    """
    return get_currency_registry().get(code)

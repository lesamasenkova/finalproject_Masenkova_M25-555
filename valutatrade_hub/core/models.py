"""
Модуль основных доменных моделей приложения.
Содержит классы User, Wallet, Portfolio для управления пользователями и их портфелями.
"""
import hashlib
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from valutatrade_hub.core.exceptions import (
    InvalidUsernameError,
    InvalidPasswordLengthError,
    InsufficientFundsError,
    InvalidAmountError,
    CurrencyAlreadyInPortfolioError,
    WalletNotFoundError,
)
from valutatrade_hub.core.currencies import get_currency


# ============= Класс Wallet =============

class Wallet:
    """
    Кошелёк для одной конкретной валюты.
    
    Хранит баланс валюты и предоставляет методы для
    пополнения, снятия и получения информации о состоянии.
    """
    
    def __init__(self, currency_code: str, initial_balance: float = 0.0):
        """
        Инициализация кошелька.
        
        Args:
            currency_code: Код валюты (например, "USD", "BTC")
            initial_balance: Начальный баланс (по умолчанию 0.0)
            
        Raises:
            InvalidAmountError: Если начальный баланс отрицательный.
        """
        # Валидируем валюту (будет выброшено CurrencyNotFoundError если её нет)
        self._currency = get_currency(currency_code)
        
        # Валидируем начальный баланс
        if initial_balance < 0:
            raise InvalidAmountError(initial_balance)
        
        self._balance = float(initial_balance)
    
    @property
    def currency_code(self) -> str:
        """Возвращает код валюты кошелька."""
        return self._currency.code
    
    @property
    def currency(self):
        """Возвращает объект валюты."""
        return self._currency
    
    @property
    def balance(self) -> float:
        """Возвращает текущий баланс кошелька."""
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        """
        Сеттер для баланса с проверками.
        
        Args:
            value: Новое значение баланса
            
        Raises:
            InvalidAmountError: Если значение отрицательное.
            TypeError: Если значение не число.
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"Баланс должен быть числом, получено: {type(value)}")
        
        if value < 0:
            raise InvalidAmountError(value)
        
        self._balance = float(value)
    
    def deposit(self, amount: float) -> None:
        """
        Пополнить баланс кошелька.
        
        Args:
            amount: Сумма пополнения (должна быть > 0)
            
        Raises:
            InvalidAmountError: Если сумма не положительная.
        """
        if amount <= 0:
            raise InvalidAmountError(amount)
        
        self._balance += float(amount)
    
    def withdraw(self, amount: float) -> None:
        """
        Снять средства с кошелька.
        
        Args:
            amount: Сумма снятия (должна быть > 0 и <= баланса)
            
        Raises:
            InvalidAmountError: Если сумма не положительная.
            InsufficientFundsError: Если недостаточно средств.
        """
        if amount <= 0:
            raise InvalidAmountError(amount)
        
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount, self.currency_code)
        
        self._balance -= float(amount)
    
    def get_balance_info(self) -> str:
        """
        Возвращает информацию о балансе в читаемом виде.
        
        Returns:
            Строка с информацией о валюте и балансе.
        """
        return f"{self.currency_code}: {self._balance:.8f}"
    
    def to_dict(self) -> Dict:
        """
        Сериализует кошелёк в словарь для сохранения в JSON.
        
        Returns:
            Словарь с данными кошелька.
        """
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "Wallet":
        """
        Десериализует кошелёк из словаря.
        
        Args:
            data: Словарь с данными кошелька.
            
        Returns:
            Объект Wallet.
        """
        return Wallet(
            currency_code=data["currency_code"],
            initial_balance=data.get("balance", 0.0),
        )
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return f"Wallet(currency='{self.currency_code}', balance={self._balance})"
    
    def __str__(self) -> str:
        """Строковое представление."""
        return self.get_balance_info()


# ============= Класс Portfolio =============

class Portfolio:
    """
    Портфель пользователя — управление всеми кошельками одного пользователя.
    
    Хранит словарь кошельков (ключ — код валюты, значение — объект Wallet)
    и предоставляет методы для управления ими.
    """
    
    def __init__(self, user_id: int, initial_wallets: Optional[Dict[str, Wallet]] = None):
        """
        Инициализация портфеля.
        
        Args:
            user_id: ID пользователя, которому принадлежит портфель.
            initial_wallets: Словарь начальных кошельков (опционально).
        """
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = initial_wallets.copy() if initial_wallets else {}
    
    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя (только чтение)."""
        return self._user_id
    
    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> Wallet:
        """
        Добавляет новый кошелёк в портфель.
        
        Args:
            currency_code: Код валюты.
            initial_balance: Начальный баланс (по умолчанию 0.0).
            
        Returns:
            Созданный объект Wallet.
            
        Raises:
            CurrencyAlreadyInPortfolioError: Если валюта уже есть в портфеле.
        """
        currency_code = currency_code.upper()
        
        if currency_code in self._wallets:
            raise CurrencyAlreadyInPortfolioError(currency_code)
        
        wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = wallet
        return wallet
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """
        Получает кошелёк по коду валюты.
        
        Args:
            currency_code: Код валюты.
            
        Returns:
            Объект Wallet.
            
        Raises:
            WalletNotFoundError: Если кошелька нет в портфеле.
        """
        currency_code = currency_code.upper()
        
        if currency_code not in self._wallets:
            raise WalletNotFoundError(currency_code)
        
        return self._wallets[currency_code]
    
    def has_wallet(self, currency_code: str) -> bool:
        """
        Проверяет, есть ли кошелёк для валюты.
        
        Args:
            currency_code: Код валюты.
            
        Returns:
            True если кошелёк есть, иначе False.
        """
        return currency_code.upper() in self._wallets
    
    def get_total_value(self, base_currency: str = "USD", exchange_rates: Optional[Dict] = None) -> float:
        """
        Возвращает общую стоимость всех валют в портфеле в базовой валюте.
        
        Args:
            base_currency: Базовая валюта для конвертации (по умолчанию "USD").
            exchange_rates: Словарь курсов вида {"USD_EUR": 0.927, "BTC_USD": 59337.21, ...}.
                          Если None, используются фиксированные курсы.
            
        Returns:
            Общая стоимость в базовой валюте.
        """
        if exchange_rates is None:
            exchange_rates = self._get_default_rates()
        
        total_value = 0.0
        base_currency = base_currency.upper()
        
        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                # Если это базовая валюта, добавляем баланс как есть
                total_value += wallet.balance
            else:
                # Ищем курс конвертации
                pair_key = f"{currency_code}_{base_currency}"
                
                if pair_key in exchange_rates:
                    rate = exchange_rates[pair_key]
                    total_value += wallet.balance * rate
                else:
                    # Если прямого курса нет, пытаемся обратный
                    reverse_pair_key = f"{base_currency}_{currency_code}"
                    if reverse_pair_key in exchange_rates:
                        rate = 1.0 / exchange_rates[reverse_pair_key]
                        total_value += wallet.balance * rate
        
        return total_value
    
    @staticmethod
    def _get_default_rates() -> Dict[str, float]:
        """
        Возвращает фиксированные курсы валют для упрощённого расчёта.
        
        Используется, если нет актуальных курсов из API.
        
        Returns:
            Словарь пар валют и их курсов.
        """
        return {
            "USD_USD": 1.0,
            "EUR_USD": 1.0786,
            "GBP_USD": 1.2704,
            "RUB_USD": 0.01016,
            "JPY_USD": 0.0067,
            "CNY_USD": 0.1379,
            "CHF_USD": 1.1250,
            "CAD_USD": 0.7350,
            "AUD_USD": 0.6504,
            "BTC_USD": 59337.21,
            "ETH_USD": 3720.00,
            "SOL_USD": 145.12,
            "XRP_USD": 2.45,
            "ADA_USD": 0.95,
            "DOT_USD": 6.88,
            "LTC_USD": 120.50,
        }
    
    def to_dict(self) -> Dict:
        """
        Сериализует портфель в словарь для сохранения в JSON.
        
        Returns:
            Словарь с данными портфеля.
        """
        return {
            "user_id": self._user_id,
            "wallets": {code: wallet.to_dict() for code, wallet in self._wallets.items()},
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "Portfolio":
        """
        Десериализует портфель из словаря.
        
        Args:
            data: Словарь с данными портфеля.
            
        Returns:
            Объект Portfolio.
        """
        user_id = data["user_id"]
        wallets = {}
        
        for currency_code, wallet_data in data.get("wallets", {}).items():
            wallets[currency_code] = Wallet.from_dict(wallet_data)
        
        return Portfolio(user_id, wallets)
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return f"Portfolio(user_id={self._user_id}, wallets={len(self._wallets)})"
    
    def __str__(self) -> str:
        """Строковое представление."""
        return f"Portfolio({len(self._wallets)} wallets)"


# ============= Класс User =============

class User:
    """
    Пользователь системы.
    
    Хранит информацию о пользователе, включая имя, хешированный пароль,
    дату регистрации и методы для работы с паролем.
    """
    
    MIN_PASSWORD_LENGTH = 4
    
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: Optional[datetime] = None,
    ):
        """
        Инициализация пользователя.
        
        Args:
            user_id: Уникальный ID пользователя.
            username: Имя пользователя (не пустое).
            hashed_password: Хешированный пароль.
            salt: Соль для хеширования пароля.
            registration_date: Дата регистрации (если None, используется текущее время).
            
        Raises:
            InvalidUsernameError: Если username пустое.
        """
        if not username or not isinstance(username, str):
            raise InvalidUsernameError()
        
        self._user_id = user_id
        self._username = username.strip()
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date or datetime.utcnow()
    
    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя."""
        return self._user_id
    
    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username
    
    @property
    def registration_date(self) -> datetime:
        """Возвращает дату регистрации."""
        return self._registration_date
    
    @property
    def salt(self) -> str:
        """Возвращает соль пароля."""
        return self._salt
    
    def verify_password(self, password: str) -> bool:
        """
        Проверяет, совпадает ли введённый пароль с хешированным.
        
        Args:
            password: Введённый пароль в открытом виде.
            
        Returns:
            True если пароль совпадает, иначе False.
        """
        hashed = self._hash_password(password, self._salt)
        return hashed == self._hashed_password
    
    def change_password(self, new_password: str) -> None:
        """
        Изменяет пароль пользователя.
        
        Args:
            new_password: Новый пароль.
            
        Raises:
            InvalidPasswordLengthError: Если пароль слишком короткий.
        """
        if len(new_password) < self.MIN_PASSWORD_LENGTH:
            raise InvalidPasswordLengthError(self.MIN_PASSWORD_LENGTH)
        
        # Генерируем новую соль
        self._salt = self._generate_salt()
        # Хешируем новый пароль с новой солью
        self._hashed_password = self._hash_password(new_password, self._salt)
    
    @staticmethod
    def _generate_salt() -> str:
        """
        Генерирует случайную соль для хеширования пароля.
        
        Returns:
            Строка с солью (случайное значение UUID).
        """
        return str(uuid4())[:12]  # Берём первые 12 символов UUID
    
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Хеширует пароль с солью.
        
        Используется алгоритм SHA-256 для одностороннего хеширования.
        
        Args:
            password: Пароль в открытом виде.
            salt: Соль для хеширования.
            
        Returns:
            Хешированный пароль (hex-строка).
        """
        combined = f"{password}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    @staticmethod
    def create_new(username: str, password: str) -> "User":
        """
        Создаёт нового пользователя с автоматической генерацией ID и хеширования пароля.
        
        Args:
            username: Имя пользователя.
            password: Пароль в открытом виде.
            
        Returns:
            Новый объект User.
            
        Raises:
            InvalidUsernameError: Если username некорректный.
            InvalidPasswordLengthError: Если пароль слишком короткий.
        """
        if not username or not isinstance(username, str):
            raise InvalidUsernameError()
        
        if len(password) < User.MIN_PASSWORD_LENGTH:
            raise InvalidPasswordLengthError(User.MIN_PASSWORD_LENGTH)
        
        user_id = int(datetime.utcnow().timestamp() * 1000) % 1000000
        salt = User._generate_salt()
        hashed_password = User._hash_password(password, salt)
        
        return User(user_id, username, hashed_password, salt)
    
    def get_user_info(self) -> Dict:
        """
        Возвращает информацию о пользователе (без пароля).
        
        Returns:
            Словарь с информацией о пользователе.
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }
    
    def to_dict(self) -> Dict:
        """
        Сериализует пользователя в словарь для сохранения в JSON.
        
        Returns:
            Словарь с данными пользователя.
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "User":
        """
        Десериализует пользователя из словаря.
        
        Args:
            data: Словарь с данными пользователя.
            
        Returns:
            Объект User.
        """
        registration_date = None
        if "registration_date" in data:
            try:
                registration_date = datetime.fromisoformat(data["registration_date"])
            except (ValueError, TypeError):
                pass
        
        return User(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=registration_date,
        )
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return f"User(user_id={self._user_id}, username='{self._username}')"
    
    def __str__(self) -> str:
        """Строковое представление."""
        return f"{self._username} (id={self._user_id})"

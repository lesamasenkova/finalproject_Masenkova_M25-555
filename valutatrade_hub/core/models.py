"""Основные модели данных приложения."""

import hashlib
import os
from datetime import datetime
from typing import Optional

from valutatrade_hub.core.exceptions import InsufficientFundsError, ValidationError


class User:
    """Класс для представления пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        """
        Инициализация пользователя.

        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            hashed_password: Хешированный пароль
            salt: Соль для хеширования
            registration_date: Дата регистрации
        """
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        """Получить ID пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Получить имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str):
        """Установить имя пользователя с валидацией."""
        if not value or not value.strip():
            raise ValidationError("Имя не может быть пустым")
        self._username = value

    @property
    def hashed_password(self) -> str:
        """Получить хешированный пароль."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Получить соль."""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Получить дату регистрации."""
        return self._registration_date

    def get_user_info(self) -> dict:
        """Получить информацию о пользователе без пароля."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str):
        """Изменить пароль пользователя."""
        if len(new_password) < 4:
            raise ValidationError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """Проверить соответствие пароля."""
        return self._hash_password(password, self._salt) == self._hashed_password

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Хешировать пароль с солью."""
        combined = password + salt
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def create_new_user(user_id: int, username: str, password: str) -> "User":
        """Создать нового пользователя с генерацией соли и хеша."""
        if not username or not username.strip():
            raise ValidationError("Имя не может быть пустым")
        if len(password) < 4:
            raise ValidationError("Пароль должен быть не короче 4 символов")

        salt = os.urandom(16).hex()
        hashed_password = User._hash_password(password, salt)
        registration_date = datetime.now()

        return User(user_id, username, hashed_password, salt, registration_date)


class Wallet:
    """Класс для представления кошелька одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """Инициализация кошелька."""
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        """Получить текущий баланс."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Установить баланс с валидацией."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValidationError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float):
        """Пополнить баланс."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValidationError("Сумма пополнения должна быть положительной")
        self._balance += amount

    def withdraw(self, amount: float):
        """
        Снять средства с баланса.

        Raises:
            InsufficientFundsError: Если недостаточно средств
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValidationError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount, self.currency_code)
        self._balance -= amount

    def get_balance_info(self) -> dict:
        """Получить информацию о балансе."""
        return {"currency_code": self.currency_code, "balance": self._balance}


class Portfolio:
    """Класс для управления портфелем пользователя."""

    def __init__(self, user_id: int, wallets: Optional[dict] = None):
        """Инициализация портфеля."""
        self._user_id = user_id
        self._wallets = {}

        if wallets:
            for currency_code, wallet_data in wallets.items():
                if isinstance(wallet_data, Wallet):
                    self._wallets[currency_code] = wallet_data
                else:
                    balance = wallet_data.get("balance", 0.0)
                    self._wallets[currency_code] = Wallet(currency_code, balance)

    @property
    def user_id(self) -> int:
        """Получить ID пользователя."""
        return self._user_id

    @property
    def wallets(self) -> dict:
        """Получить копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        """Добавить новую валюту в портфель."""
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            raise ValidationError(f"Кошелек {currency_code} уже существует")
        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """Получить кошелек по коду валюты."""
        return self._wallets.get(currency_code.upper())

    def get_total_value(
        self, base_currency: str = "USD", exchange_rates: Optional[dict] = None
    ) -> float:
        """Получить общую стоимость портфеля в базовой валюте."""
        if not exchange_rates:
            exchange_rates = {}

        total = 0.0
        base_currency = base_currency.upper()

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    rate = exchange_rates[rate_key].get("rate", 0)
                    total += wallet.balance * rate

        return total

    def to_dict(self) -> dict:
        """Преобразовать портфель в словарь для сохранения."""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = {"balance": wallet.balance}
        return {"user_id": self._user_id, "wallets": wallets_dict}

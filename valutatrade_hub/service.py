"""
Модуль бизнес-логики приложения (Service Layer).
Содержит основные операции: регистрация, авторизация, управление портфелем, конвертация.
"""
from typing import Dict
from datetime import datetime

from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.decorators import log_action, catch_and_log
from valutatrade_hub.core.models import User, Portfolio, Wallet
from valutatrade_hub.core.utils import (
    validate_amount,
    validate_currency_code,
    calculate_conversion_details,
    format_currency_amount,
)
from valutatrade_hub.core.exceptions import (
    AuthenticationError,
    UserNotFoundError,
)
from valutatrade_hub.infra.database import get_database


class UserService:
    """
    Сервис для управления пользователями.
    
    Операции: регистрация, авторизация, смена пароля, получение информации.
    """
    
    def __init__(self):
        """Инициализация сервиса."""
        self.logger = get_logger(__name__)
        self.db = get_database()
    
    @log_action
    def register_user(self, username: str, password: str) -> User:
        """
        Регистрирует нового пользователя.
        
        Args:
            username: Имя пользователя.
            password: Пароль.
            
        Returns:
            Созданный объект User.
            
        Raises:
            InvalidUsernameError: Если username некорректен.
            InvalidPasswordLengthError: Если пароль слишком короткий.
        """
        # Проверяем, не существует ли пользователь
        if self.db.user_exists(username):
            raise ValueError(f"User '{username}' already exists")
        
        # Создаём нового пользователя
        user = User.create_new(username, password)
        
        # Добавляем в БД
        self.db.add_user(user)
        
        # Создаём пустой портфель
        portfolio = Portfolio(user.user_id)
        self.db.add_portfolio(portfolio)
        
        self.logger.info(f"User '{username}' registered successfully")
        return user
    
    @log_action
    def authenticate(self, username: str, password: str) -> User:
        """
        Проверяет учётные данные пользователя.
        
        Args:
            username: Имя пользователя.
            password: Пароль.
            
        Returns:
            Объект User если аутентификация успешна.
            
        Raises:
            AuthenticationError: Если пароль неверен или пользователь не найден.
        """
        user = self.db.get_user(username)
        
        if user is None:
            raise AuthenticationError(f"User '{username}' not found")
        
        if not user.verify_password(password):
            raise AuthenticationError("Invalid password")
        
        self.logger.info(f"User '{username}' authenticated successfully")
        return user
    
    @log_action
    def change_password(self, username: str, old_password: str, new_password: str) -> None:
        """
        Меняет пароль пользователя.
        
        Args:
            username: Имя пользователя.
            old_password: Старый пароль.
            new_password: Новый пароль.
            
        Raises:
            AuthenticationError: Если старый пароль неверен.
            InvalidPasswordLengthError: Если новый пароль слишком короткий.
        """
        # Проверяем старый пароль
        user = self.authenticate(username, old_password)
        
        # Меняем пароль
        user.change_password(new_password)
        
        # Сохраняем
        self.db.update_user(user)
        
        self.logger.info(f"Password changed for user '{username}'")
    
    @log_action
    def get_user_info(self, username: str) -> Dict:
        """
        Получает информацию о пользователе.
        
        Args:
            username: Имя пользователя.
            
        Returns:
            Словарь с информацией о пользователе.
            
        Raises:
            UserNotFoundError: Если пользователь не найден.
        """
        user = self.db.get_user(username)
        
        if user is None:
            raise UserNotFoundError(username)
        
        return user.get_user_info()


class PortfolioService:
    """
    Сервис для управления портфелями и кошельками.
    
    Операции: добавление валюты, пополнение, снятие, просмотр баланса.
    """
    
    def __init__(self):
        """Инициализация сервиса."""
        self.logger = get_logger(__name__)
        self.db = get_database()
    
    @log_action
    def add_currency_to_portfolio(self, username: str, currency_code: str, 
                                   initial_balance: float = 0.0) -> Wallet:
        """
        Добавляет валюту в портфель пользователя.
        
        Args:
            username: Имя пользователя.
            currency_code: Код валюты.
            initial_balance: Начальный баланс.
            
        Returns:
            Созданный объект Wallet.
            
        Raises:
            UserNotFoundError: Если пользователь не найден.
        """
        user = self.db.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        
        # Получаем портфель
        portfolio = self.db.get_portfolio(user.user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user.user_id}")
        
        # Добавляем валюту
        wallet = portfolio.add_currency(currency_code, initial_balance)
        
        # Сохраняем
        self.db.update_portfolio(portfolio)
        
        self.logger.info(
            f"Currency '{currency_code}' added to portfolio of '{username}'"
        )
        return wallet
    
    @log_action
    def deposit(self, username: str, currency_code: str, amount: float) -> float:
        """
        Пополняет баланс валюты в портфеле пользователя.
        
        Args:
            username: Имя пользователя.
            currency_code: Код валюты.
            amount: Сумма пополнения.
            
        Returns:
            Новый баланс.
            
        Raises:
            UserNotFoundError: Если пользователь не найден.
        """
        amount = validate_amount(amount)
        
        user = self.db.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        
        portfolio = self.db.get_portfolio(user.user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user.user_id}")
        
        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        
        self.db.update_portfolio(portfolio)
        
        self.logger.info(
            f"Deposited {format_currency_amount(amount, currency_code)} "
            f"to {username}"
        )
        return wallet.balance
    
    @log_action
    def withdraw(self, username: str, currency_code: str, amount: float) -> float:
        """
        Снимает средства с баланса валюты в портфеле пользователя.
        
        Args:
            username: Имя пользователя.
            currency_code: Код валюты.
            amount: Сумма снятия.
            
        Returns:
            Новый баланс.
            
        Raises:
            UserNotFoundError: Если пользователь не найден.
        """
        amount = validate_amount(amount)
        
        user = self.db.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        
        portfolio = self.db.get_portfolio(user.user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user.user_id}")
        
        wallet = portfolio.get_wallet(currency_code)
        wallet.withdraw(amount)
        
        self.db.update_portfolio(portfolio)
        
        self.logger.info(
            f"Withdrawn {format_currency_amount(amount, currency_code)} "
            f"from {username}"
        )
        return wallet.balance
    
    @log_action
    def get_wallet_info(self, username: str, currency_code: str) -> Dict:
        """
        Получает информацию о кошельке пользователя.
        
        Args:
            username: Имя пользователя.
            currency_code: Код валюты.
            
        Returns:
            Словарь с информацией о кошельке.
        """
        user = self.db.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        
        portfolio = self.db.get_portfolio(user.user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user.user_id}")
        
        wallet = portfolio.get_wallet(currency_code)
        
        return {
            "currency": wallet.currency_code,
            "balance": wallet.balance,
            "balance_formatted": wallet.get_balance_info(),
        }
    
    @log_action
    def get_portfolio_summary(self, username: str) -> Dict:
        """
        Получает обзор всего портфеля пользователя.
        
        Args:
            username: Имя пользователя.
            
        Returns:
            Словарь с информацией о портфеле.
        """
        user = self.db.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        
        portfolio = self.db.get_portfolio(user.user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user.user_id}")
        
        wallets_info = []
        for currency_code, wallet in portfolio.wallets.items():
            wallets_info.append({
                "currency": currency_code,
                "balance": wallet.balance,
                "balance_formatted": wallet.get_balance_info(),
            })
        
        # Получаем общую стоимость портфеля
        exchange_rates = self.db.get_all_exchange_rates()
        total_value = portfolio.get_total_value("USD", exchange_rates)
        
        return {
            "username": username,
            "wallets": wallets_info,
            "total_value_usd": total_value,
            "wallet_count": len(wallets_info),
        }


class ConversionService:
    """
    Сервис для конвертации валют.
    
    Операции: расчёт курса, выполнение конвертации, получение курсов.
    """
    
    def __init__(self):
        """Инициализация сервиса."""
        self.logger = get_logger(__name__)
        self.db = get_database()
    
    @log_action
    def get_conversion_rate(self, from_code: str, to_code: str) -> float:
        """
        Получает текущий курс обмена между двумя валютами.
        
        Args:
            from_code: Исходная валюта.
            to_code: Целевая валюта.
            
        Returns:
            Курс обмена.
            
        Raises:
            ValueError: Если курс не найден.
        """
        from_code = validate_currency_code(from_code)
        to_code = validate_currency_code(to_code)
        
        if from_code == to_code:
            return 1.0
        
        rates = self.db.get_all_exchange_rates()
        
        # Ищем прямой курс
        pair_key = f"{from_code}_{to_code}"
        if pair_key in rates:
            return rates[pair_key]
        
        # Ищем обратный курс
        reverse_pair_key = f"{to_code}_{from_code}"
        if reverse_pair_key in rates:
            return 1.0 / rates[reverse_pair_key]
        
        raise ValueError(f"Exchange rate {from_code}→{to_code} not found")
    
    @log_action
    def calculate_conversion(self, amount: float, from_code: str, 
                           to_code: str) -> Dict:
        """
        Рассчитывает конвертацию между валютами.
        
        Args:
            amount: Сумма для конвертации.
            from_code: Исходная валюта.
            to_code: Целевая валюта.
            
        Returns:
            Словарь с деталями конвертации.
        """
        amount = validate_amount(amount, allow_zero=True)
        rates = self.db.get_all_exchange_rates()
        
        return calculate_conversion_details(amount, from_code, to_code, rates)
    
    @log_action
    def exchange_in_portfolio(self, username: str, from_code: str, 
                             to_code: str, amount: float) -> Dict:
        """
        Выполняет обмен валют в портфеле пользователя.
        
        Снимает сумму из одной валюты и добавляет в другую.
        
        Args:
            username: Имя пользователя.
            from_code: Исходная валюта.
            to_code: Целевая валюта.
            amount: Сумма для обмена.
            
        Returns:
            Словарь с результатом операции.
            
        Raises:
            UserNotFoundError: Если пользователь не найден.
        """
        amount = validate_amount(amount)
        
        user = self.db.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        
        portfolio = self.db.get_portfolio(user.user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user.user_id}")
        
        # Рассчитываем конвертацию
        conversion = self.calculate_conversion(amount, from_code, to_code)
        
        # Снимаем из исходной валюты
        from_wallet = portfolio.get_wallet(from_code)
        from_wallet.withdraw(amount)
        
        # Добавляем в целевую валюту
        to_wallet = portfolio.get_wallet(to_code)
        to_wallet.deposit(conversion["result"])
        
        # Сохраняем портфель
        self.db.update_portfolio(portfolio)
        
        self.logger.info(
            f"Exchanged {format_currency_amount(amount, from_code)} "
            f"to {format_currency_amount(conversion['result'], to_code)} "
            f"for user '{username}'"
        )
        
        return {
            "success": True,
            "from_currency": from_code,
            "from_amount": amount,
            "to_currency": to_code,
            "to_amount": conversion["result"],
            "rate": conversion["rate"],
            "from_balance": from_wallet.balance,
            "to_balance": to_wallet.balance,
        }
    
    @log_action
    def update_exchange_rates(self, rates: Dict[str, float]) -> None:
        """
        Обновляет курсы обмена в БД.
        
        Args:
            rates: Словарь с новыми курсами.
        """
        self.db.update_exchange_rates(rates)
        self.logger.info(f"Updated {len(rates)} exchange rates")
    
    @log_action
    def get_all_rates(self) -> Dict[str, float]:
        """
        Получает все доступные курсы обмена.
        
        Returns:
            Словарь всех курсов.
        """
        return self.db.get_all_exchange_rates()


class ApplicationService:
    """
    Главный сервис приложения.
    
    Координирует работу всех остальных сервисов.
    """
    
    def __init__(self):
        """Инициализация главного сервиса."""
        self.logger = get_logger(__name__)
        self.users = UserService()
        self.portfolio = PortfolioService()
        self.conversion = ConversionService()
    
    @log_action
    def get_application_info(self) -> Dict:
        """
        Получает информацию о приложении и состояние БД.
        
        Returns:
            Словарь с информацией.
        """
        db = get_database()
        stats = db.get_statistics()
        
        return {
            "app_name": "ValutaTrade Hub",
            "version": "0.1.0",
            "database": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @catch_and_log
    def backup_database(self) -> bool:
        """
        Синхронизирует БД (сохраняет всё на диск).
        
        Returns:
            True если успешно, False если ошибка.
        """
        db = get_database()
        db.sync()
        self.logger.info("Database backed up")
        return True

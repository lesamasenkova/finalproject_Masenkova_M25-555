"""
Модуль пользовательских исключений для ValutaTrade Hub.
Содержит все доменные ошибки, используемые в приложении.
"""


class ValutaTradeException(Exception):
    """Базовое исключение для всех ошибок приложения."""
    pass


class AuthenticationError(ValutaTradeException):
    """Ошибки аутентификации и авторизации."""
    pass


class UserNotFoundError(AuthenticationError):
    """Пользователь не найден в системе."""
    
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Пользователь '{username}' не найден")


class InvalidPasswordError(AuthenticationError):
    """Неверный пароль."""
    
    def __init__(self):
        super().__init__("Неверный пароль")


class UsernameAlreadyExistsError(AuthenticationError):
    """Имя пользователя уже занято."""
    
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Имя пользователя '{username}' уже занято")


class InvalidPasswordLengthError(AuthenticationError):
    """Пароль слишком короткий."""
    
    def __init__(self, min_length: int = 4):
        super().__init__(f"Пароль должен быть не короче {min_length} символов")


class InvalidUsernameError(AuthenticationError):
    """Некорректное имя пользователя."""
    
    def __init__(self):
        super().__init__("Имя пользователя не может быть пустым")


# ============= Ошибки валют и кошельков =============

class CurrencyError(ValutaTradeException):
    """Ошибки, связанные с валютами."""
    pass


class CurrencyNotFoundError(CurrencyError):
    """Неизвестная валюта."""
    
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class InvalidCurrencyCodeError(CurrencyError):
    """Некорректный код валюты."""
    
    def __init__(self, code: str, reason: str = ""):
        self.code = code
        msg = f"Некорректный код валюты '{code}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class WalletError(ValutaTradeException):
    """Ошибки работы с кошельками."""
    pass


class InsufficientFundsError(WalletError):
    """Недостаточно средств на кошельке."""
    
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(
            f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        )


class InvalidAmountError(WalletError):
    """Некорректная сумма (отрицательная или ноль)."""
    
    def __init__(self, amount: float):
        self.amount = amount
        super().__init__(f"Сумма должна быть положительным числом, получено: {amount}")


class WalletNotFoundError(WalletError):
    """Кошелёк для валюты не найден."""
    
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(
            f"У вас нет кошелька '{currency_code}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )


class PortfolioError(ValutaTradeException):
    """Ошибки работы с портфелем."""
    pass


class CurrencyAlreadyInPortfolioError(PortfolioError):
    """Валюта уже есть в портфеле."""
    
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Валюта '{currency_code}' уже есть в портфеле")


# ============= Ошибки API и внешних сервисов =============

class ExternalServiceError(ValutaTradeException):
    """Ошибки при работе с внешними сервисами."""
    pass


class ApiRequestError(ExternalServiceError):
    """Ошибка при обращении к внешнему API."""
    
    def __init__(self, service_name: str, reason: str):
        self.service_name = service_name
        self.reason = reason
        super().__init__(
            f"Ошибка при обращении к {service_name}: {reason}"
        )


class RateNotAvailableError(ExternalServiceError):
    """Курс валюты недоступен."""
    
    def __init__(self, from_code: str, to_code: str):
        self.from_code = from_code
        self.to_code = to_code
        super().__init__(
            f"Курс {from_code}→{to_code} недоступен. Повторите попытку позже."
        )


class RateCacheExpiredError(ExternalServiceError):
    """Кэш курсов устарел."""
    
    def __init__(self, from_code: str, to_code: str, last_update: str):
        super().__init__(
            f"Курс {from_code}→{to_code} устарел "
            f"(последнее обновление: {last_update}). "
            f"Выполните 'update-rates' для актуализации."
        )


# ============= Ошибки данных и хранилища =============

class DataError(ValutaTradeException):
    """Ошибки работы с данными."""
    pass


class DataFileNotFoundError(DataError):
    """Файл данных не найден."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Файл данных не найден: {file_path}")


class CorruptedDataError(DataError):
    """Данные повреждены или некорректны."""
    
    def __init__(self, file_path: str, reason: str = ""):
        self.file_path = file_path
        msg = f"Данные в файле {file_path} повреждены"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class DatabaseError(DataError):
    """Ошибка при работе с хранилищем."""
    
    def __init__(self, message: str):
        super().__init__(f"Ошибка базы данных: {message}")


# ============= Ошибки конфигурации =============

class ConfigurationError(ValutaTradeException):
    """Ошибки конфигурации приложения."""
    pass


class SettingsError(ConfigurationError):
    """Ошибка загрузки или применения настроек."""
    
    def __init__(self, message: str):
        super().__init__(f"Ошибка конфигурации: {message}")

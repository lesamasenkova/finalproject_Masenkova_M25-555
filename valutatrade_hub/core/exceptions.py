"""Пользовательские исключения приложения."""


class InsufficientFundsError(Exception):
    """Исключение при недостатке средств."""

    def __init__(self, available: float, required: float, currency_code: str):
        """
        Инициализация исключения.

        Args:
            available: Доступная сумма
            required: Требуемая сумма
            currency_code: Код валюты
        """
        self.available = available
        self.required = required
        self.currency_code = currency_code
        message = (
            f"Недостаточно средств: доступно {available} {currency_code}, "
            f"требуется {required} {currency_code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Исключение при обращении к неизвестной валюте."""

    def __init__(self, currency_code: str):
        """
        Инициализация исключения.

        Args:
            currency_code: Код неизвестной валюты
        """
        self.currency_code = currency_code
        message = f"Неизвестная валюта '{currency_code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Исключение при ошибке обращения к внешнему API."""

    def __init__(self, reason: str):
        """
        Инициализация исключения.

        Args:
            reason: Причина ошибки
        """
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class ValidationError(Exception):
    """Исключение при ошибке валидации данных."""

    pass

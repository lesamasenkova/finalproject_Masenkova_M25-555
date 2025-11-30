"""
Модуль вспомогательных функций для валидации и конвертации.
Содержит утилиты для работы с валютами, суммами и курсами обмена.
"""
from typing import Dict, Tuple
from valutatrade_hub.core.exceptions import (
    InvalidAmountError,
    InvalidCurrencyCodeError,
    CurrencyNotFoundError,
)
from valutatrade_hub.core.currencies import get_currency


# ============= Валидация сумм =============

def validate_amount(amount: float, allow_zero: bool = False) -> float:
    """
    Валидирует сумму (должна быть положительным числом).
    
    Args:
        amount: Сумма для валидации.
        allow_zero: Разрешить ли нулевое значение (по умолчанию False).
        
    Returns:
        Валидная сумма как float.
        
    Raises:
        InvalidAmountError: Если сумма некорректна.
        TypeError: Если тип не число.
    """
    if not isinstance(amount, (int, float)):
        raise TypeError(f"Сумма должна быть числом, получено: {type(amount).__name__}")
    
    if allow_zero:
        if amount < 0:
            raise InvalidAmountError(amount)
    else:
        if amount <= 0:
            raise InvalidAmountError(amount)
    
    return float(amount)


def validate_amounts(*amounts: float, allow_zero: bool = False) -> Tuple[float, ...]:
    """
    Валидирует несколько сумм одновременно.
    
    Args:
        *amounts: Переменное количество сумм.
        allow_zero: Разрешить ли нулевые значения.
        
    Returns:
        Кортеж валидных сумм.
        
    Raises:
        InvalidAmountError: Если любая сумма некорректна.
    """
    return tuple(validate_amount(amt, allow_zero) for amt in amounts)


# ============= Валидация кодов валют =============

def validate_currency_code(code: str) -> str:
    """
    Валидирует код валюты и возвращает его в стандартном виде.
    
    Args:
        code: Код валюты (например, "btc", "USD").
        
    Returns:
        Валидный код валюты в верхнем регистре.
        
    Raises:
        InvalidCurrencyCodeError: Если код некорректен.
        CurrencyNotFoundError: Если валюта не найдена в реестре.
    """
    if not isinstance(code, str):
        raise InvalidCurrencyCodeError(str(code), "код должен быть строкой")
    
    code = code.strip().upper()
    
    if not (2 <= len(code) <= 5):
        raise InvalidCurrencyCodeError(
            code,
            "код должен быть 2-5 символов"
        )
    
    if not code.isalnum():
        raise InvalidCurrencyCodeError(
            code,
            "код должен содержать только буквы и цифры"
        )
    
    # Проверяем, существует ли валюта в реестре
    try:
        get_currency(code)
    except CurrencyNotFoundError:
        raise
    
    return code


def validate_currency_pair(from_code: str, to_code: str) -> Tuple[str, str]:
    """
    Валидирует пару валют для конвертации.
    
    Args:
        from_code: Исходная валюта.
        to_code: Целевая валюта.
        
    Returns:
        Кортеж (from_code, to_code) в стандартном виде.
        
    Raises:
        InvalidCurrencyCodeError или CurrencyNotFoundError: Если коды некорректны.
    """
    from_validated = validate_currency_code(from_code)
    to_validated = validate_currency_code(to_code)
    return (from_validated, to_validated)


# ============= Конвертация валют =============

def get_exchange_rate(
    from_code: str,
    to_code: str,
    rates: Dict[str, float]
) -> float:
    """
    Получает курс обмена из словаря курсов.
    
    Пытается найти как прямой курс, так и обратный (для вычисления).
    
    Args:
        from_code: Исходная валюта.
        to_code: Целевая валюта.
        rates: Словарь курсов вида {"USD_EUR": 0.927, "BTC_USD": 59337.21}.
        
    Returns:
        Курс обмена (сколько to_code стоит 1 from_code).
        
    Raises:
        ValueError: Если курс не найден ни в прямом, ни в обратном виде.
    """
    from_code = from_code.upper()
    to_code = to_code.upper()
    
    # Если это одна и та же валюта
    if from_code == to_code:
        return 1.0
    
    # Ищем прямой курс
    pair_key = f"{from_code}_{to_code}"
    if pair_key in rates:
        return rates[pair_key]
    
    # Ищем обратный курс
    reverse_pair_key = f"{to_code}_{from_code}"
    if reverse_pair_key in rates:
        return 1.0 / rates[reverse_pair_key]
    
    raise ValueError(
        f"Курс {from_code}→{to_code} не найден в словаре курсов"
    )


def convert_amount(
    amount: float,
    from_code: str,
    to_code: str,
    rates: Dict[str, float]
) -> float:
    """
    Конвертирует сумму из одной валюты в другую.
    
    Args:
        amount: Сумма для конвертации.
        from_code: Исходная валюта.
        to_code: Целевая валюта.
        rates: Словарь курсов.
        
    Returns:
        Конвертированная сумма.
        
    Raises:
        InvalidAmountError: Если сумма некорректна.
        ValueError: Если курс не найден.
    """
    amount = validate_amount(amount, allow_zero=True)
    rate = get_exchange_rate(from_code, to_code, rates)
    return amount * rate


def calculate_conversion_details(
    amount: float,
    from_code: str,
    to_code: str,
    rates: Dict[str, float]
) -> Dict:
    """
    Рассчитывает детали конвертации (курс и результат).
    
    Args:
        amount: Сумма.
        from_code: Исходная валюта.
        to_code: Целевая валюта.
        rates: Словарь курсов.
        
    Returns:
        Словарь с детальной информацией:
        {
            "amount": 0.05,
            "from_currency": "BTC",
            "to_currency": "USD",
            "rate": 59337.21,
            "result": 2966.86,
            "formatted": "0.0500 BTC = 2966.86 USD (курс: 59337.21)"
        }
    """
    from_code = validate_currency_code(from_code)
    to_code = validate_currency_code(to_code)
    amount = validate_amount(amount, allow_zero=True)
    
    rate = get_exchange_rate(from_code, to_code, rates)
    result = amount * rate
    
    formatted = (
        f"{amount:.8f} {from_code} = {result:.8f} {to_code} "
        f"(курс: {rate:.8f})"
    )
    
    return {
        "amount": amount,
        "from_currency": from_code,
        "to_currency": to_code,
        "rate": rate,
        "result": result,
        "formatted": formatted,
    }


# ============= Форматирование =============

def format_currency_amount(
    amount: float,
    currency_code: str,
    decimals: int = 2,
    separator: str = " "
) -> str:
    """
    Форматирует сумму в валюте для отображения.
    
    Args:
        amount: Сумма.
        currency_code: Код валюты.
        decimals: Количество знаков после запятой (по умолчанию 2).
        separator: Разделитель между суммой и кодом (по умолчанию пробел).
        
    Returns:
        Отформатированная строка (например, "100.50 USD").
    """
    amount = validate_amount(amount, allow_zero=True)
    currency_code = validate_currency_code(currency_code)
    
    return f"{amount:.{decimals}f}{separator}{currency_code}"


def format_percentage_change(
    old_value: float,
    new_value: float,
    decimals: int = 2
) -> str:
    """
    Форматирует процент изменения между двумя значениями.
    
    Args:
        old_value: Старое значение.
        new_value: Новое значение.
        decimals: Количество знаков после запятой.
        
    Returns:
        Строка с процентом изменения (например, "+5.25%" или "-3.10%").
    """
    if old_value == 0:
        return "N/A"
    
    percentage = ((new_value - old_value) / old_value) * 100
    sign = "+" if percentage > 0 else ""
    
    return f"{sign}{percentage:.{decimals}f}%"


# ============= Парсинг пользовательского ввода =============

def parse_currency_input(user_input: str) -> str:
    """
    Парсит и валидирует ввод пользователя для кода валюты.
    
    Удаляет пробелы, переводит в верхний регистр, валидирует.
    
    Args:
        user_input: Входная строка от пользователя.
        
    Returns:
        Валидный код валюты.
        
    Raises:
        InvalidCurrencyCodeError или CurrencyNotFoundError.
    """
    return validate_currency_code(user_input.strip())


def parse_amount_input(user_input: str, allow_zero: bool = False) -> float:
    """
    Парсит и валидирует ввод пользователя для суммы.
    
    Args:
        user_input: Входная строка от пользователя.
        allow_zero: Разрешить ли нулевое значение.
        
    Returns:
        Валидная сумма как float.
        
    Raises:
        ValueError: Если парсинг не удался.
        InvalidAmountError: Если сумма некорректна.
    """
    try:
        amount = float(user_input.strip())
    except ValueError:
        raise ValueError(f"'{user_input}' не является числом")
    
    return validate_amount(amount, allow_zero)


# ============= Работа со словарями курсов =============

def merge_exchange_rates(*rate_dicts: Dict[str, float]) -> Dict[str, float]:
    """
    Объединяет несколько словарей курсов, приоритет левым аргументам.
    
    Args:
        *rate_dicts: Переменное количество словарей курсов.
        
    Returns:
        Объединённый словарь.
    """
    result = {}
    for rate_dict in rate_dicts:
        result.update(rate_dict)
    return result


def filter_rates_by_currency(
    rates: Dict[str, float],
    currency_code: str,
    direction: str = "both"
) -> Dict[str, float]:
    """
    Фильтрует словарь курсов по конкретной валюте.
    
    Args:
        rates: Исходный словарь курсов.
        currency_code: Код валюты для фильтра.
        direction: "from" (где валюта исходная),
                  "to" (где валюта целевая),
                  "both" (в обоих направлениях).
        
    Returns:
        Отфильтрованный словарь.
    """
    currency_code = validate_currency_code(currency_code)
    result = {}
    
    for pair, rate in rates.items():
        from_code, to_code = pair.split("_")
        
        if direction in ("from", "both") and from_code == currency_code:
            result[pair] = rate
        elif direction in ("to", "both") and to_code == currency_code:
            result[pair] = rate
    
    return result


def get_rate_pair_string(
    from_code: str,
    to_code: str,
    rate: float,
    decimals: int = 2
) -> str:
    """
    Форматирует информацию о курсе в читаемую строку.
    
    Args:
        from_code: Исходная валюта.
        to_code: Целевая валюта.
        rate: Курс.
        decimals: Знаков после запятой.
        
    Returns:
        Форматированная строка (например, "1 BTC = 59337.21 USD").
    """
    from_code = validate_currency_code(from_code)
    to_code = validate_currency_code(to_code)
    
    return f"1 {from_code} = {rate:.{decimals}f} {to_code}"

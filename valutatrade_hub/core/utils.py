"""Вспомогательные функции для работы с данными."""

from datetime import datetime
from typing import Optional

from valutatrade_hub.core.currencies import get_currency, is_currency_supported
from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


def find_user_by_username(username: str) -> Optional[User]:
    """
    Найти пользователя по имени.
    
    Args:
        username: Имя пользователя
        
    Returns:
        Объект User или None
    """
    db = DatabaseManager()
    users = db.load_users()
    for user in users:
        if user.username == username:
            return user
    return None


def find_user_by_id(user_id: int) -> Optional[User]:
    """
    Найти пользователя по ID.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Объект User или None
    """
    db = DatabaseManager()
    users = db.load_users()
    for user in users:
        if user.user_id == user_id:
            return user
    return None


def get_next_user_id() -> int:
    """
    Получить следующий свободный ID пользователя.
    
    Returns:
        Новый ID (автоинкремент)
    """
    db = DatabaseManager()
    users = db.load_users()
    if not users:
        return 1
    return max(user.user_id for user in users) + 1


def find_portfolio_by_user_id(user_id: int) -> Optional[Portfolio]:
    """
    Найти портфель пользователя по ID.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Объект Portfolio или None
    """
    db = DatabaseManager()
    portfolios = db.load_portfolios()
    for portfolio in portfolios:
        if portfolio.user_id == user_id:
            return portfolio
    return None


def validate_currency_code(code: str) -> str:
    """
    Валидировать код валюты.
    
    Args:
        code: Код валюты
        
    Returns:
        Нормализованный код (верхний регистр)
        
    Raises:
        CurrencyNotFoundError: Если валюта не поддерживается
    """
    code = code.upper().strip()
    
    if not is_currency_supported(code):
        raise CurrencyNotFoundError(code)
    
    return code


def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
    """
    Получить курс обмена валют.
    
    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта
        
    Returns:
        Курс обмена или None
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    # Валидируем коды валют
    from_currency = validate_currency_code(from_currency)
    to_currency = validate_currency_code(to_currency)

    # Если одна и та же валюта - курс 1:1
    if from_currency == to_currency:
        return 1.0

    db = DatabaseManager()
    rates = db.load_rates()
    rate_key = f"{from_currency}_{to_currency}"

    # Прямой курс
    if rate_key in rates and isinstance(rates[rate_key], dict):
        return rates[rate_key].get("rate")

    # Обратный курс
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates and isinstance(rates[reverse_key], dict):
        reverse_rate = rates[reverse_key].get("rate")
        if reverse_rate and reverse_rate != 0:
            return 1.0 / reverse_rate

    return None


def is_rates_cache_fresh() -> bool:
    """
    Проверить, свежий ли кеш курсов.
    
    Returns:
        True если кеш свежий
    """
    settings = SettingsLoader()
    ttl_seconds = settings.get("rates_ttl_seconds", 300)
    
    db = DatabaseManager()
    rates = db.load_rates()
    
    last_refresh = rates.get("last_refresh")
    if not last_refresh:
        return False
    
    try:
        last_refresh_dt = datetime.fromisoformat(last_refresh)
        age_seconds = (datetime.now() - last_refresh_dt).total_seconds()
        return age_seconds < ttl_seconds
    except Exception:
        return False


def get_rate_with_ttl_check(from_currency: str, to_currency: str) -> tuple:
    """
    Получить курс с проверкой TTL.
    
    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта
        
    Returns:
        Кортеж (курс, время_обновления, предупреждение)
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена
        ApiRequestError: Если кеш устарел и не удалось обновить
    """
    rate = get_exchange_rate(from_currency, to_currency)
    
    if rate is None:
        raise ApiRequestError(f"Курс {from_currency}→{to_currency} недоступен")
    
    db = DatabaseManager()
    rates = db.load_rates()
    rate_key = f"{from_currency}_{to_currency}"
    
    updated_at = "неизвестно"
    if rate_key in rates and isinstance(rates[rate_key], dict):
        updated_at = rates[rate_key].get("updated_at", "неизвестно")
    
    warning = None
    if not is_rates_cache_fresh():
        warning = "⚠️  Курсы устарели. Рекомендуется выполнить 'update-rates'"
    
    return rate, updated_at, warning


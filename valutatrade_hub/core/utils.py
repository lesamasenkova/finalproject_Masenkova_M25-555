"""Вспомогательные функции для работы с данными."""

from datetime import datetime
from typing import Optional

from valutatrade_hub.core.currencies import is_currency_supported
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
    Получить курс обмена валют из кеша.
    Поддерживает кросс-курсы через USD.

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
    rates_data = db.load_rates()

    # Проверяем структуру
    if not rates_data or not isinstance(rates_data, dict):
        return None

    if "pairs" not in rates_data:
        return None

    pairs = rates_data["pairs"]
    if not isinstance(pairs, dict):
        return None

    # Вспомогательная функция для извлечения курса
    def get_direct_rate(from_c: str, to_c: str) -> Optional[float]:
        rate_key = f"{from_c}_{to_c}"
        # Прямой курс
        if rate_key in pairs:
            pair_data = pairs[rate_key]
            if isinstance(pair_data, dict) and "rate" in pair_data:
                rate = pair_data["rate"]
                if isinstance(rate, (int, float)) and rate > 0:
                    return float(rate)

        # Обратный курс
        reverse_key = f"{to_c}_{from_c}"
        if reverse_key in pairs:
            pair_data = pairs[reverse_key]
            if isinstance(pair_data, dict) and "rate" in pair_data:
                reverse_rate = pair_data["rate"]
                if isinstance(reverse_rate, (int, float)) and reverse_rate > 0:
                    return 1.0 / float(reverse_rate)

        return None

    # Пытаемся найти прямой курс
    direct_rate = get_direct_rate(from_currency, to_currency)
    if direct_rate is not None:
        return direct_rate

    # Если прямого курса нет, пытаемся найти кросс-курс через USD
    if from_currency != "USD" and to_currency != "USD":
        from_to_usd = get_direct_rate(from_currency, "USD")
        to_to_usd = get_direct_rate(to_currency, "USD")

        if from_to_usd is not None and to_to_usd is not None and to_to_usd > 0:
            # Например: BTC→EUR = (BTC→USD) / (EUR→USD)
            return from_to_usd / to_to_usd

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
        ApiRequestError: Если курс недоступен
    """
    rate = get_exchange_rate(from_currency, to_currency)
    if rate is None:
        raise ApiRequestError(f"Курс {from_currency}→{to_currency} недоступен")

    db = DatabaseManager()
    rates_data = db.load_rates()

    rate_key = f"{from_currency}_{to_currency}"
    reverse_key = f"{to_currency}_{from_currency}"
    updated_at = "неизвестно"

    if "pairs" in rates_data:
        pairs = rates_data["pairs"]
        if rate_key in pairs and isinstance(pairs[rate_key], dict):
            updated_at = pairs[rate_key].get("updated_at", "неизвестно")
        elif reverse_key in pairs and isinstance(pairs[reverse_key], dict):
            updated_at = pairs[reverse_key].get("updated_at", "неизвестно")
        else:
            # Для кросс-курсов берем время обновления USD
            usd_key_from = f"{from_currency}_USD"
            if usd_key_from in pairs and isinstance(pairs[usd_key_from], dict):
                updated_at = pairs[usd_key_from].get("updated_at", "неизвестно")

    warning = None
    if not is_rates_cache_fresh():
        warning = "⚠️ Курсы устарели. Рекомендуется выполнить 'update-rates'"

    return rate, updated_at, warning


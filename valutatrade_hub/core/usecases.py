"""Бизнес-логика приложения."""

from typing import Optional, Tuple

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    ValidationError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    find_portfolio_by_user_id,
    find_user_by_username,
    get_next_user_id,
    get_rate_with_ttl_check,
    validate_currency_code,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager


class AuthService:
    """Сервис аутентификации пользователей."""

    _current_user: Optional[User] = None

    @classmethod
    @log_action("REGISTER")
    def register(cls, username: str, password: str) -> Tuple[bool, str]:
        """
        Зарегистрировать нового пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Проверка уникальности имени
            if find_user_by_username(username):
                return False, f"Имя пользователя '{username}' уже занято"

            # Создание нового пользователя
            user_id = get_next_user_id()
            new_user = User.create_new_user(user_id, username, password)

            # Сохранение пользователя
            db = DatabaseManager()
            users = db.load_users()
            users.append(new_user)
            db.save_users(users)

            # Создание пустого портфеля
            portfolios = db.load_portfolios()
            new_portfolio = Portfolio(user_id)
            portfolios.append(new_portfolio)
            db.save_portfolios(portfolios)

            return (
                True,
                f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****",
            )
        except ValidationError as e:
            return False, str(e)

    @classmethod
    @log_action("LOGIN")
    def login(cls, username: str, password: str) -> Tuple[bool, str]:
        """
        Войти в систему.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Кортеж (успех, сообщение)
        """
        user = find_user_by_username(username)
        if not user:
            return False, f"Пользователь '{username}' не найден"

        if not user.verify_password(password):
            return False, "Неверный пароль"

        cls._current_user = user
        return True, f"Вы вошли как '{username}'"

    @classmethod
    def get_current_user(cls) -> Optional[User]:
        """Получить текущего пользователя."""
        return cls._current_user

    @classmethod
    def is_logged_in(cls) -> bool:
        """Проверить, залогинен ли пользователь."""
        return cls._current_user is not None

    @classmethod
    def logout(cls):
        """Выйти из системы."""
        cls._current_user = None


class PortfolioService:
    """Сервис управления портфелем."""

    @staticmethod
    def show_portfolio(base_currency: str = "USD") -> Tuple[bool, str]:
        """
        Показать портфель текущего пользователя.

        Args:
            base_currency: Базовая валюта для отображения

        Returns:
            Кортеж (успех, сообщение)
        """
        if not AuthService.is_logged_in():
            return False, "Сначала выполните login"

        try:
            # Валидация базовой валюты
            base_currency = validate_currency_code(base_currency)
        except CurrencyNotFoundError as e:
            return False, f"{str(e)}. Используйте команду 'help' для списка валют."

        user = AuthService.get_current_user()
        portfolio = find_portfolio_by_user_id(user.user_id)

        if not portfolio:
            return True, f"Портфель пользователя '{user.username}' пуст.\nИспользуйте команду 'buy' для покупки валюты."

        wallets = portfolio.wallets
        if not wallets:
            return True, f"Портфель пользователя '{user.username}' пуст"

        # Формируем вывод
        output = [f"Портфель пользователя '{user.username}' (база: {base_currency}):"]
        total = 0.0

        for currency_code, wallet in wallets.items():
            balance = wallet.balance
            try:
                if currency_code == base_currency:
                    value_in_base = balance
                else:
                    from valutatrade_hub.core.utils import get_exchange_rate

                    rate = get_exchange_rate(currency_code, base_currency)
                    if rate:
                        value_in_base = balance * rate
                    else:
                        output.append(
                            f"- {currency_code}: {balance:.4f} → курс недоступен"
                        )
                        continue

                total += value_in_base
                # Получаем информацию о валюте
                output.append(
                    f"- {currency_code}: {balance:.4f} → {value_in_base:.2f} {base_currency}"
                )
            except CurrencyNotFoundError:
                output.append(f"- {currency_code}: {balance:.4f} → неизвестная валюта")

        output.append("---------------------------------")
        output.append(f"ИТОГО: {total:,.2f} {base_currency}")

        return True, "\n".join(output)

    @staticmethod
    @log_action("BUY")
    def buy_currency(currency: str, amount: float) -> Tuple[bool, str]:
        """
        Купить валюту.

        Args:
            currency: Код валюты
            amount: Количество

        Returns:
            Кортеж (успех, сообщение)
        """
        if not AuthService.is_logged_in():
            return False, "Сначала выполните login"

        try:
            # Валидация валюты
            currency = validate_currency_code(currency)

            # Валидация количества
            if not isinstance(amount, (int, float)) or amount <= 0:
                raise ValidationError("'amount' должен быть положительным числом")

            user = AuthService.get_current_user()
            db = DatabaseManager()
            portfolios = db.load_portfolios()

            portfolio = None
            for p in portfolios:
                if p.user_id == user.user_id:
                    portfolio = p
                    break

            # Создаем портфель, если его нет
            if not portfolio:
                portfolio = Portfolio(user.user_id)
                portfolios.append(portfolio)

            # Получаем информацию о валюте
            currency_obj = get_currency(currency)

            # Если кошелька нет - создаем
            wallet = portfolio.get_wallet(currency)
            old_balance = 0.0
            if not wallet:
                portfolio.add_currency(currency)
                wallet = portfolio.get_wallet(currency)
            else:
                old_balance = wallet.balance

            # Пополняем баланс
            wallet.deposit(amount)
            new_balance = wallet.balance

            # Сохраняем изменения
            db.save_portfolios(portfolios)

            # Получаем курс для отчета
            try:
                from valutatrade_hub.core.utils import get_exchange_rate

                rate = get_exchange_rate(currency, "USD")
                if rate:
                    cost = amount * rate
                    output = [
                        f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}",
                        f"Валюта: {currency_obj.get_display_info()}",
                        "Изменения в портфеле:",
                        f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}",
                        f"Оценочная стоимость покупки: {cost:,.2f} USD",
                    ]
                else:
                    output = [
                        f"Покупка выполнена: {amount:.4f} {currency}",
                        f"Валюта: {currency_obj.get_display_info()}",
                        "Изменения в портфеле:",
                        f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}",
                        "Курс для оценки недоступен",
                    ]
            except Exception:
                output = [
                    f"Покупка выполнена: {amount:.4f} {currency}",
                    "Изменения в портфеле:",
                    f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}",
                ]

            return True, "\n".join(output)

        except CurrencyNotFoundError as e:
            return (
                False,
                f"{str(e)}. Используйте команду 'help' для списка поддерживаемых валют.",
            )
        except ValidationError as e:
            return False, str(e)

    @staticmethod
    @log_action("SELL")
    def sell_currency(currency: str, amount: float) -> Tuple[bool, str]:
        """
        Продать валюту.

        Args:
            currency: Код валюты
            amount: Количество

        Returns:
            Кортеж (успех, сообщение)
        """
        if not AuthService.is_logged_in():
            return False, "Сначала выполните login"

        try:
            # Валидация валюты
            currency = validate_currency_code(currency)

            # Валидация количества
            if not isinstance(amount, (int, float)) or amount <= 0:
                raise ValidationError("'amount' должен быть положительным числом")

            user = AuthService.get_current_user()
            db = DatabaseManager()
            portfolios = db.load_portfolios()

            portfolio = None
            for p in portfolios:
                if p.user_id == user.user_id:
                    portfolio = p
                    break

            if not portfolio:
                return False, "Портфель пуст. Сначала купите валюту командой 'buy --currency BTC --amount 0.001'"

            # Получаем информацию о валюте
            currency_obj = get_currency(currency)
            wallet = portfolio.get_wallet(currency)

            if not wallet:
                return (
                    False,
                    f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.",
                )

            old_balance = wallet.balance

            # Попытка снятия
            wallet.withdraw(amount)
            new_balance = wallet.balance

            # Сохраняем изменения
            db.save_portfolios(portfolios)

            # Получаем курс для отчета
            try:
                from valutatrade_hub.core.utils import get_exchange_rate

                rate = get_exchange_rate(currency, "USD")
                if rate:
                    revenue = amount * rate
                    output = [
                        f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}",
                        f"Валюта: {currency_obj.get_display_info()}",
                        "Изменения в портфеле:",
                        f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}",
                        f"Оценочная выручка: {revenue:,.2f} USD",
                    ]
                else:
                    output = [
                        f"Продажа выполнена: {amount:.4f} {currency}",
                        f"Валюта: {currency_obj.get_display_info()}",
                        "Изменения в портфеле:",
                        f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}",
                        "Курс для оценки недоступен",
                    ]
            except Exception:
                output = [
                    f"Продажа выполнена: {amount:.4f} {currency}",
                    "Изменения в портфеле:",
                    f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}",
                ]

            return True, "\n".join(output)

        except CurrencyNotFoundError as e:
            return (
                False,
                f"{str(e)}. Используйте команду 'help' для списка поддерживаемых валют.",
            )
        except InsufficientFundsError as e:
            return False, str(e)
        except ValidationError as e:
            return False, str(e)


class RatesService:
    """Сервис получения курсов валют."""

    @staticmethod
    def get_rate(from_currency: str, to_currency: str) -> Tuple[bool, str]:
        """
        Получить курс валюты.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Валидация через get_currency
            from_curr_obj = get_currency(from_currency)
            to_curr_obj = get_currency(to_currency)

            # Получаем курс с проверкой TTL
            rate, updated_at, warning = get_rate_with_ttl_check(
                from_curr_obj.code, to_curr_obj.code
            )

            reverse_rate = 1.0 / rate if rate != 0 else 0
            output = [
                f"Из: {from_curr_obj.get_display_info()}",
                f"В: {to_curr_obj.get_display_info()}",
                f"Курс {from_curr_obj.code}→{to_curr_obj.code}: {rate:.8f} (обновлено: {updated_at})",
                f"Обратный курс {to_curr_obj.code}→{from_curr_obj.code}: {reverse_rate:.8f}",
            ]

            if warning:
                output.append(warning)

            return True, "\n".join(output)

        except CurrencyNotFoundError as e:
            from valutatrade_hub.core.currencies import get_all_currency_codes

            supported = ", ".join(get_all_currency_codes())
            return False, f"{str(e)}\n\nПоддерживаемые валюты: {supported}"
        except ApiRequestError as e:
            return (
                False,
                f"{str(e)}\n\nПовторите попытку позже или выполните 'update-rates'",
            )


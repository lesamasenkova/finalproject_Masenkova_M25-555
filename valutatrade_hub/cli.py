"""
Модуль CLI интерфейса приложения ValutaTrade Hub.
Интерактивное меню для работы с приложением.
"""
from valuatatrade_hub.logging_config import get_logger
from valuatatrade_hub.service import ApplicationService
from valuatatrade_hub.core.exceptions import (
    AuthenticationError,
    CurrencyNotFoundError,
)


logger = get_logger(__name__)
app_service = ApplicationService()
current_user = None


def print_menu(title: str, options: dict) -> str:
    """Выводит меню и получает выбор пользователя."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    for key, value in options.items():
        print(f"  {key}. {value}")
    print(f"{'='*70}")
    choice = input("\n➜ Выберите пункт меню: ").strip()
    return choice


def print_header(text: str) -> None:
    """Выводит заголовок."""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}\n")


def print_success(text: str) -> None:
    """Выводит сообщение об успехе."""
    print(f"\n✅ {text}\n")


def print_error(text: str) -> None:
    """Выводит сообщение об ошибке."""
    print(f"\n❌ {text}\n")


def print_info(text: str) -> None:
    """Выводит информационное сообщение."""
    print(f"\nℹ️  {text}\n")


def auth_menu() -> bool:
    """Меню аутентификации."""
    global current_user
    options = {"1": "Регистрация", "2": "Вход", "0": "Выход"}
    while True:
        choice = print_menu("🔐 АУТЕНТИФИКАЦИЯ", options)
        if choice == "1":
            register_user()
        elif choice == "2":
            if login_user():
                return True
        elif choice == "0":
            print("\n👋 До встречи!\n")
            return False
        else:
            print_error("Неверный выбор")


def register_user() -> None:
    """Регистрирует нового пользователя."""
    print_header("📝 РЕГИСТРАЦИЯ")
    username = input("Имя пользователя: ").strip()
    if not username:
        print_error("Имя пользователя не может быть пустым")
        return
    password = input("Пароль (мин. 6 символов): ").strip()
    if not password:
        print_error("Пароль не может быть пустым")
        return
    try:
        app_service.users.register_user(username, password)
        print_success(f"Пользователь '{username}' успешно зарегистрирован!")
    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Ошибка регистрации: {e}")


def login_user() -> bool:
    """Авторизует пользователя."""
    global current_user
    print_header("🔑 ВХОД")
    username = input("Имя пользователя: ").strip()
    if not username:
        print_error("Имя пользователя не может быть пустым")
        return False
    password = input("Пароль: ").strip()
    if not password:
        print_error("Пароль не может быть пустым")
        return False
    try:
        current_user = app_service.users.authenticate(username, password)
        print_success(f"Добро пожаловать, {username}!")
        return True
    except AuthenticationError as e:
        print_error(f"Ошибка аутентификации: {e}")
        return False
    except Exception as e:
        print_error(f"Ошибка при входе: {e}")
        return False


def main_menu() -> None:
    """Главное меню приложения."""
    options = {"1": "👤 Профиль", "2": "💼 Портфель", "3": "💱 Конвертация", "4": "ℹ️  О приложении", "5": "🚪 Выход"}
    while True:
        choice = print_menu(f"🏠 ГЛАВНОЕ МЕНЮ (пользователь: {current_user.username})", options)
        if choice == "1":
            profile_menu()
        elif choice == "2":
            portfolio_menu()
        elif choice == "3":
            conversion_menu()
        elif choice == "4":
            show_app_info()
        elif choice == "5":
            logout_user()
            break
        else:
            print_error("Неверный выбор")


def profile_menu() -> None:
    """Меню профиля пользователя."""
    options = {"1": "📋 Просмотреть информацию", "2": "🔐 Смена пароля", "0": "Назад"}
    while True:
        choice = print_menu("👤 ПРОФИЛЬ", options)
        if choice == "1":
            show_user_info()
        elif choice == "2":
            change_password()
        elif choice == "0":
            break
        else:
            print_error("Неверный выбор")


def show_user_info() -> None:
    """Показывает информацию о пользователе."""
    print_header("📋 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
    try:
        info = app_service.users.get_user_info(current_user.username)
        print(f"Имя пользователя: {info['username']}")
        print(f"ID: {info['user_id']}")
        print(f"Создан: {info['created_at']}")
        print(f"Последний вход: {info['last_login']}")
    except Exception as e:
        print_error(f"Ошибка при получении информации: {e}")


def change_password() -> None:
    """Меняет пароль пользователя."""
    print_header("🔐 СМЕНА ПАРОЛЯ")
    old_password = input("Текущий пароль: ").strip()
    if not old_password:
        print_error("Пароль не может быть пустым")
        return
    new_password = input("Новый пароль (мин. 6 символов): ").strip()
    if not new_password:
        print_error("Пароль не может быть пустым")
        return
    try:
        app_service.users.change_password(current_user.username, old_password, new_password)
        print_success("Пароль успешно изменён!")
    except AuthenticationError as e:
        print_error(f"Ошибка: {e}")
    except Exception as e:
        print_error(f"Ошибка при смене пароля: {e}")


def portfolio_menu() -> None:
    """Меню управления портфелем."""
    options = {"1": "📊 Просмотреть портфель", "2": "➕ Добавить валюту", "3": "💰 Пополнить баланс", "4": "💸 Снять средства", "5": "📈 Информация о кошельке", "0": "Назад"}
    while True:
        choice = print_menu("💼 ПОРТФЕЛЬ", options)
        if choice == "1":
            show_portfolio()
        elif choice == "2":
            add_currency()
        elif choice == "3":
            deposit_funds()
        elif choice == "4":
            withdraw_funds()
        elif choice == "5":
            show_wallet_info()
        elif choice == "0":
            break
        else:
            print_error("Неверный выбор")


def show_portfolio() -> None:
    """Показывает портфель пользователя."""
    print_header("📊 ВАШ ПОРТФЕЛЬ")
    try:
        summary = app_service.portfolio.get_portfolio_summary(current_user.username)
        print(f"Кошельков: {summary['wallet_count']}")
        print(f"Общая стоимость в USD: ${summary['total_value_usd']:.2f}\n")
        print("Кошельки:\n" + "─" * 50)
        for wallet in summary['wallets']:
            print(f"  {wallet['currency']:6} │ Баланс: {wallet['balance_formatted']}")
        print("─" * 50)
    except Exception as e:
        print_error(f"Ошибка при получении портфеля: {e}")


def add_currency() -> None:
    """Добавляет новую валюту в портфель."""
    print_header("➕ ДОБАВИТЬ ВАЛЮТУ")
    currency_code = input("Код валюты (например, USD, EUR, BTC): ").strip().upper()
    if not currency_code:
        print_error("Код валюты не может быть пустым")
        return
    try:
        initial_balance = float(input("Начальный баланс (по умолчанию 0): ").strip() or "0")
    except ValueError:
        print_error("Неверный формат суммы")
        return
    try:
        app_service.portfolio.add_currency_to_portfolio(current_user.username, currency_code, initial_balance)
        print_success(f"Валюта '{currency_code}' добавлена в портфель!")
    except CurrencyNotFoundError:
        print_error(f"Валюта '{currency_code}' не поддерживается")
    except Exception as e:
        print_error(f"Ошибка при добавлении валюты: {e}")


def deposit_funds() -> None:
    """Пополняет баланс валюты."""
    print_header("💰 ПОПОЛНИТЬ БАЛАНС")
    currency_code = input("Код валюты: ").strip().upper()
    try:
        amount = float(input("Сумма для пополнения: ").strip())
    except ValueError:
        print_error("Неверный формат суммы")
        return
    try:
        new_balance = app_service.portfolio.deposit(current_user.username, currency_code, amount)
        print_success(f"Счёт пополнен! Новый баланс: {new_balance}")
    except Exception as e:
        print_error(f"Ошибка при пополнении: {e}")


def withdraw_funds() -> None:
    """Снимает средства со счёта."""
    print_header("💸 СНЯТЬ СРЕДСТВА")
    currency_code = input("Код валюты: ").strip().upper()
    try:
        amount = float(input("Сумма для снятия: ").strip())
    except ValueError:
        print_error("Неверный формат суммы")
        return
    try:
        new_balance = app_service.portfolio.withdraw(current_user.username, currency_code, amount)
        print_success(f"Средства сняты! Новый баланс: {new_balance}")
    except Exception as e:
        print_error(f"Ошибка при снятии: {e}")


def show_wallet_info() -> None:
    """Показывает информацию о конкретном кошельке."""
    print_header("📈 ИНФОРМАЦИЯ О КОШЕЛЬКЕ")
    currency_code = input("Код валюты: ").strip().upper()
    try:
        info = app_service.portfolio.get_wallet_info(current_user.username, currency_code)
        print(f"Валюта: {info['currency']}")
        print(f"Баланс: {info['balance_formatted']}")
    except Exception as e:
        print_error(f"Ошибка при получении информации: {e}")


def conversion_menu() -> None:
    """Меню конвертации валют."""
    options = {"1": "📊 Получить курс", "2": "🧮 Рассчитать конвертацию", "3": "💱 Выполнить обмен", "4": "📈 Все курсы", "0": "Назад"}
    while True:
        choice = print_menu("💱 КОНВЕРТАЦИЯ", options)
        if choice == "1":
            get_rate()
        elif choice == "2":
            calculate_conversion()
        elif choice == "3":
            perform_exchange()
        elif choice == "4":
            show_all_rates()
        elif choice == "0":
            break
        else:
            print_error("Неверный выбор")


def get_rate() -> None:
    """Получает курс обмена между двумя валютами."""
    print_header("📊 ПОЛУЧИТЬ КУРС")
    from_code = input("Из валюты: ").strip().upper()
    to_code = input("В валюту: ").strip().upper()
    try:
        rate = app_service.conversion.get_conversion_rate(from_code, to_code)
        print_info(f"1 {from_code} = {rate:.8f} {to_code}")
    except Exception as e:
        print_error(f"Ошибка при получении курса: {e}")


def calculate_conversion() -> None:
    """Рассчитывает конвертацию между валютами."""
    print_header("🧮 РАССЧИТАТЬ КОНВЕРТАЦИЮ")
    from_code = input("Из валюты: ").strip().upper()
    to_code = input("В валюту: ").strip().upper()
    try:
        amount = float(input("Сумма: ").strip())
    except ValueError:
        print_error("Неверный формат суммы")
        return
    try:
        result = app_service.conversion.calculate_conversion(amount, from_code, to_code)
        print(f"\nИсходная сумма: {result['amount']:.8f} {result['from_currency']}")
        print(f"Результат: {result['result']:.8f} {result['to_currency']}")
        print(f"Курс: {result['rate']:.8f}")
    except Exception as e:
        print_error(f"Ошибка при расчёте: {e}")


def perform_exchange() -> None:
    """Выполняет обмен валют в портфеле пользователя."""
    print_header("💱 ВЫПОЛНИТЬ ОБМЕН")
    from_code = input("Из валюты: ").strip().upper()
    to_code = input("В валюту: ").strip().upper()
    try:
        amount = float(input("Сумма для обмена: ").strip())
    except ValueError:
        print_error("Неверный формат суммы")
        return
    try:
        result = app_service.conversion.exchange_in_portfolio(current_user.username, from_code, to_code, amount)
        print("\n✅ Обмен выполнен!")
        print(f"Отправлено: {result['from_amount']:.8f} {result['from_currency']}")
        print(f"Получено: {result['to_amount']:.8f} {result['to_currency']}")
        print(f"Курс: {result['rate']:.8f}")
        print(f"Новый баланс {from_code}: {result['from_balance']:.8f}")
        print(f"Новый баланс {to_code}: {result['to_balance']:.8f}")
    except Exception as e:
        print_error(f"Ошибка при обмене: {e}")


def show_all_rates() -> None:
    """Показывает все доступные курсы обмена."""
    print_header("📈 ВСЕ КУРСЫ ОБМЕНА")
    try:
        rates = app_service.conversion.get_all_rates()
        if not rates:
            print_info("Курсы не загружены")
            return
        print(f"Всего курсов: {len(rates)}\n" + "Курсы:\n" + "─" * 50)
        for pair, rate in sorted(rates.items()):
            print(f"  {pair:15} │ {rate:.8f}")
        print("─" * 50)
    except Exception as e:
        print_error(f"Ошибка при получении курсов: {e}")


def show_app_info() -> None:
    """Показывает информацию о приложении."""
    print_header("ℹ️  О ПРИЛОЖЕНИИ")
    try:
        info = app_service.get_application_info()
        print(f"Приложение: {info['app_name']}\nВерсия: {info['version']}\n")
        print("База данных:")
        print(f"  • Пользователей: {info['database']['users_count']}")
        print(f"  • Портфелей: {info['database']['portfolios_count']}")
        print(f"  • Курсов: {info['database']['exchange_rates_count']}")
    except Exception as e:
        print_error(f"Ошибка при получении информации: {e}")


def logout_user() -> None:
    """Выходит из аккаунта."""
    global current_user
    print_success(f"До встречи, {current_user.username}!")
    current_user = None


def run_cli() -> None:
    """Запускает CLI приложение."""
    print("\n" + "="*70)
    print("  💱 ДОБРО ПОЖАЛОВАТЬ В ValutaTrade Hub! 💱")
    print("="*70)
    if auth_menu():
        main_menu()
    print("\n" + "="*70)
    print("  Спасибо за использование ValutaTrade Hub!")
    print("="*70 + "\n")

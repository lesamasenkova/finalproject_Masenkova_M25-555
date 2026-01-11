"""Командный интерфейс приложения."""

import shlex
import sys

from valutatrade_hub.core.currencies import get_all_currency_codes
from valutatrade_hub.core.usecases import AuthService, PortfolioService, RatesService


class CLI:
    """Командный интерфейс для управления кошельком."""

    def __init__(self):
        """Инициализация CLI."""
        self.commands = {
            "register": self.cmd_register,
            "login": self.cmd_login,
            "logout": self.cmd_logout,
            "show-portfolio": self.cmd_show_portfolio,
            "buy": self.cmd_buy,
            "sell": self.cmd_sell,
            "get-rate": self.cmd_get_rate,
            "list-currencies": self.cmd_list_currencies,
            "update-rates": self.cmd_update_rates,      
            "show-rates": self.cmd_show_rates,          
            "help": self.cmd_help,
            "exit": self.cmd_exit,
        }

    def parse_args(self, args_list):
        """Парсинг аргументов команды."""
        result = {}
        i = 0
        while i < len(args_list):
            if args_list[i].startswith("--"):
                key = args_list[i][2:]
                if i + 1 < len(args_list) and not args_list[i + 1].startswith("--"):
                    value = args_list[i + 1]
                    result[key] = value
                    i += 2
                else:
                    result[key] = True
                    i += 1
            else:
                i += 1
        return result

    def cmd_register(self, args):
        """Команда регистрации пользователя."""
        username = args.get("username")
        password = args.get("password")

        if not username:
            print("Ошибка: не указан --username")
            return
        if not password:
            print("Ошибка: не указан --password")
            return

        success, message = AuthService.register(username, password)
        print(message)

    def cmd_login(self, args):
        """Команда входа в систему."""
        username = args.get("username")
        password = args.get("password")

        if not username:
            print("Ошибка: не указан --username")
            return
        if not password:
            print("Ошибка: не указан --password")
            return

        success, message = AuthService.login(username, password)
        print(message)

    def cmd_logout(self, args):
        """Команда выхода из системы."""
        if not AuthService.is_logged_in():
            print("Вы не залогинены")
            return

        user = AuthService.get_current_user()
        AuthService.logout()
        print(f"Вы вышли из аккаунта '{user.username}'")

    def cmd_show_portfolio(self, args):
        """Команда показа портфеля."""
        base = args.get("base", "USD")
        success, message = PortfolioService.show_portfolio(base)
        print(message)

    def cmd_buy(self, args):
        """Команда покупки валюты."""
        currency = args.get("currency")
        amount_str = args.get("amount")

        if not currency:
            print("Ошибка: не указан --currency")
            print("Используйте 'list-currencies' для просмотра поддерживаемых валют")
            return
        if not amount_str:
            print("Ошибка: не указан --amount")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            print("Ошибка: amount должен быть числом")
            return

        success, message = PortfolioService.buy_currency(currency, amount)
        print(message)

    def cmd_sell(self, args):
        """Команда продажи валюты."""
        currency = args.get("currency")
        amount_str = args.get("amount")

        if not currency:
            print("Ошибка: не указан --currency")
            print("Используйте 'list-currencies' для просмотра поддерживаемых валют")
            return
        if not amount_str:
            print("Ошибка: не указан --amount")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            print("Ошибка: amount должен быть числом")
            return

        success, message = PortfolioService.sell_currency(currency, amount)
        print(message)

    def cmd_get_rate(self, args):
        """Команда получения курса валюты."""
        from_currency = args.get("from")
        to_currency = args.get("to")

        if not from_currency:
            print("Ошибка: не указан --from")
            print("Используйте 'list-currencies' для просмотра поддерживаемых валют")
            return
        if not to_currency:
            print("Ошибка: не указан --to")
            print("Используйте 'list-currencies' для просмотра поддерживаемых валют")
            return

        success, message = RatesService.get_rate(from_currency, to_currency)
        print(message)

    def cmd_list_currencies(self, args):
        """Показать список поддерживаемых валют."""
        from valutatrade_hub.core.currencies import get_currency
        
        codes = get_all_currency_codes()
        
        print("\nПоддерживаемые валюты:")
        print("=" * 70)
        
        # Разделяем на фиат и крипто
        fiat = []
        crypto = []
        
        for code in sorted(codes):
            currency = get_currency(code)
            info = currency.get_display_info()
            if info.startswith("[FIAT]"):
                fiat.append(info)
            else:
                crypto.append(info)
        
        print("\nФиатные валюты:")
        for info in fiat:
            print(f"  {info}")
        
        print("\nКриптовалюты:")
        for info in crypto:
            print(f"  {info}")
        
        print("=" * 70)

    def cmd_help(self, args):
        """Показать справку по командам."""
        help_text = """
Доступные команды:

register --username <имя> --password <пароль>
    Зарегистрировать нового пользователя

login --username <имя> --password <пароль>
    Войти в систему

logout
    Выйти из системы

show-portfolio [--base <валюта>]
    Показать портфель (по умолчанию в USD)

buy --currency <код> --amount <количество>
    Купить валюту

sell --currency <код> --amount <количество>
    Продать валюту

get-rate --from <валюта> --to <валюта>
    Получить курс обмена

list-currencies
    Показать список поддерживаемых валют

update-rates [--source <coingecko|exchangerate>]
    Обновить курсы валют из внешних API

show-rates [--currency <код>] [--top <N>] [--base <валюта>]
    Показать курсы из локального кеша

help
    Показать эту справку

exit
    Выйти из приложения
"""
        print(help_text)

        print(help_text)

    def cmd_exit(self, args):
        """Выход из приложения."""
        print("До свидания!")
        sys.exit(0)

    def run(self):
        """Запуск главного цикла CLI."""
        print("=" * 70)
        print("Добро пожаловать в валютный кошелек ValutaTrade Hub!")
        print("=" * 70)
        print("Введите 'help' для получения справки")
        print("Введите 'list-currencies' для списка поддерживаемых валют")
        print()

        while True:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                # Парсим команду
                try:
                    parts = shlex.split(user_input)
                except ValueError:
                    parts = user_input.split()

                if not parts:
                    continue

                command = parts[0].lower()
                args = self.parse_args(parts[1:])

                if command in self.commands:
                    self.commands[command](args)
                else:
                    print(f"Неизвестная команда: {command}")
                    print("Введите 'help' для получения справки")

            except KeyboardInterrupt:
                print("\nИспользуйте 'exit' для выхода")
            except EOFError:
                print("\nДо свидания!")
                break
            except Exception as e:
                print(f"Ошибка: {e}")


def main():
    """Точка входа для Poetry scripts."""
    # Инициализируем логирование
    from valutatrade_hub import logging_config
    
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()

    def cmd_update_rates(self, args):
        """Команда обновления курсов валют."""
        source = args.get("source")

        print("INFO: Starting rates update...")

        try:
            from valutatrade_hub.parser_service.config import ParserConfig
            from valutatrade_hub.parser_service.api_clients import (
                CoinGeckoClient,
                ExchangeRateApiClient,
            )
            from valutatrade_hub.parser_service.storage import RatesStorage
            from valutatrade_hub.parser_service.updater import RatesUpdater

            # Инициализация
            config = ParserConfig()
            
            # Валидация конфигурации
            try:
                config.validate()
            except ValueError as e:
                print(f"ERROR: {e}")
                return

            # Создаем клиенты
            clients = [
                CoinGeckoClient(config),
                ExchangeRateApiClient(config),
            ]

            # Создаем storage
            storage = RatesStorage(config.RATES_FILE_PATH, config.HISTORY_FILE_PATH)

            # Создаем updater
            updater = RatesUpdater(clients, storage)

            # Запускаем обновление
            result = updater.run_update(source_filter=source)

            # Выводим результаты
            if result["success"]:
                print(f"INFO: Fetching from CoinGecko... OK ({len([p for p in result.get('successful_sources', []) if 'CoinGecko' in p])} sources)")
                print(f"INFO: Fetching from ExchangeRate-API... OK ({len([p for p in result.get('successful_sources', []) if 'ExchangeRate' in p])} sources)")
                print(f"INFO: Writing {result['total_rates']} rates to data/rates.json...")
                print(f"Update successful. Total rates updated: {result['total_rates']}. Last refresh: {result['timestamp']}")
            else:
                print("ERROR: Update failed")

            # Выводим ошибки
            if result["errors"]:
                print("\nErrors encountered:")
                for error in result["errors"]:
                    print(f"  - {error}")
                print("\nUpdate completed with errors. Check logs/actions.log for details.")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

    def cmd_show_rates(self, args):
        """Команда показа курсов из кеша."""
        currency = args.get("currency")
        top_str = args.get("top")
        base = args.get("base", "USD").upper()

        try:
            from valutatrade_hub.infra.database import DatabaseManager

            db = DatabaseManager()
            rates_data = db.load_rates()

            # Проверяем наличие данных
            if not rates_data or "pairs" not in rates_data or not rates_data["pairs"]:
                print("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
                return

            pairs = rates_data["pairs"]
            last_refresh = rates_data.get("last_refresh", "неизвестно")

            # Фильтрация по валюте
            if currency:
                currency = currency.upper()
                filtered_pairs = {
                    pair: info
                    for pair, info in pairs.items()
                    if currency in pair
                }
                if not filtered_pairs:
                    print(f"Курс для '{currency}' не найден в кеше.")
                    return
                pairs = filtered_pairs

            # Фильтрация по топ-N
            if top_str:
                try:
                    top_n = int(top_str)
                    # Сортируем по курсу (по убыванию) и берем топ-N
                    sorted_pairs = sorted(
                        pairs.items(), key=lambda x: x[1].get("rate", 0), reverse=True
                    )
                    pairs = dict(sorted_pairs[:top_n])
                except ValueError:
                    print(f"Ошибка: --top должен быть числом")
                    return

            # Вывод
            print(f"Rates from cache (updated at {last_refresh}):")
            for pair, info in pairs.items():
                rate = info.get("rate", 0)
                source = info.get("source", "Unknown")
                print(f"- {pair}: {rate:.8f} (source: {source})")

        except Exception as e:
            print(f"ERROR: {e}")


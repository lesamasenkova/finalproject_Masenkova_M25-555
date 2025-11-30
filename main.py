"""
Главная точка входа приложения ValutaTrade Hub.
"""
import sys
from valutatrade_hub.cli.interface import CLI


def main():
    """Запуск CLI приложения."""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Точка входа в приложение."""

from valutatrade_hub.cli.interface import CLI


def main():
    """Главная функция приложения."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()


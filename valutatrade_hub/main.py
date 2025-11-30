"""
Точка входа приложения ValutaTrade Hub.
Инициализирует приложение и запускает CLI интерфейс.
"""
import sys

from valuatatrade_hub.logging_config import initialize_logging
from valuatatrade_hub.infra.settings import get_settings
from valuatatrade_hub.infra.database import get_database
from valuatatrade_hub.cli import run_cli


def initialize_app() -> None:
    """
    Инициализирует приложение.
    
    Загружает настройки, инициализирует логирование и БД.
    """
    logger = initialize_logging()
    logger.info("=" * 70)
    logger.info("🚀 ValutaTrade Hub Starting...")
    logger.info("=" * 70)
    
    settings = get_settings()
    
    if not settings.validate():
        logger.error("Settings validation failed")
        sys.exit(1)
    
    logger.info(f"Environment: {settings.get('app.environment')}")
    logger.info(f"Version: {settings.get('app.version')}")
    
    db = get_database()
    stats = db.get_statistics()
    
    logger.info(f"Database: Users={stats['users_count']}, "
                f"Portfolios={stats['portfolios_count']}, "
                f"Rates={stats['exchange_rates_count']}")


def main() -> int:
    """
    Главная функция приложения.
    
    Returns:
        Код выхода (0 для успеха, 1 для ошибки).
    """
    try:
        initialize_app()
        run_cli()
        return 0
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return 0
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

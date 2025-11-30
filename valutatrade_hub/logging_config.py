"""
Модуль конфигурации логирования для приложения.
Настраивает логирование в файл и консоль с форматированием.
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


class LoggerConfig:
    """
    Класс для конфигурации и инициализации логирования приложения.
    
    Создаёт логеры с обработчиками для консоли и файла логов.
    """
    
    # Константы
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / "app.log"
    LOG_LEVEL_DEFAULT = logging.INFO
    LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s - %(message)s"
    LOG_FORMAT_DETAILED = (
        "%(asctime)s [%(levelname)-8s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    MAX_BYTES = 5 * 1024 * 1024  # 5 MB
    BACKUP_COUNT = 5  # Хранить 5 файлов
    
    @staticmethod
    def ensure_log_dir() -> Path:
        """
        Создаёт директорию для логов, если её нет.
        
        Returns:
            Путь к директории логов.
        """
        LoggerConfig.LOG_DIR.mkdir(exist_ok=True)
        return LoggerConfig.LOG_DIR
    
    @staticmethod
    def get_console_handler(level: int = logging.INFO) -> logging.StreamHandler:
        """
        Создаёт обработчик логов для консоли.
        
        Args:
            level: Уровень логирования (по умолчанию INFO).
            
        Returns:
            StreamHandler для вывода в консоль.
        """
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Форматер для консоли (более компактный)
        formatter = logging.Formatter(
            LoggerConfig.LOG_FORMAT,
            datefmt=LoggerConfig.DATE_FORMAT
        )
        handler.setFormatter(formatter)
        
        return handler
    
    @staticmethod
    def get_file_handler(
        log_file: Path,
        level: int = logging.DEBUG
    ) -> logging.handlers.RotatingFileHandler:
        """
        Создаёт обработчик логов для файла с ротацией.
        
        Args:
            log_file: Путь к файлу логов.
            level: Уровень логирования (по умолчанию DEBUG).
            
        Returns:
            RotatingFileHandler для логирования в файл.
        """
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LoggerConfig.MAX_BYTES,
            backupCount=LoggerConfig.BACKUP_COUNT,
            encoding="utf-8"
        )
        handler.setLevel(level)
        
        # Форматер для файла (подробный)
        formatter = logging.Formatter(
            LoggerConfig.LOG_FORMAT_DETAILED,
            datefmt=LoggerConfig.DATE_FORMAT
        )
        handler.setFormatter(formatter)
        
        return handler
    
    @staticmethod
    def setup_logger(
        name: str,
        level: int = logging.INFO,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        use_file: bool = True
    ) -> logging.Logger:
        """
        Настраивает и возвращает логер для модуля.
        
        Args:
            name: Имя логера (обычно __name__ модуля).
            level: Общий уровень логирования.
            console_level: Уровень для консоли.
            file_level: Уровень для файла.
            use_file: Использовать ли логирование в файл.
            
        Returns:
            Настроенный объект Logger.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Очищаем существующие обработчики (для переинициализации)
        logger.handlers.clear()
        
        # Добавляем обработчик консоли
        console_handler = LoggerConfig.get_console_handler(console_level)
        logger.addHandler(console_handler)
        
        # Добавляем обработчик файла, если требуется
        if use_file:
            LoggerConfig.ensure_log_dir()
            file_handler = LoggerConfig.get_file_handler(
                LoggerConfig.LOG_FILE,
                file_level
            )
            logger.addHandler(file_handler)
        
        # Предотвращаем распространение логов на родительские логеры
        logger.propagate = False
        
        return logger
    
    @staticmethod
    def setup_root_logger(
        level: int = logging.INFO,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG
    ) -> logging.Logger:
        """
        Настраивает корневой логер приложения.
        
        Args:
            level: Общий уровень логирования.
            console_level: Уровень для консоли.
            file_level: Уровень для файла.
            
        Returns:
            Настроенный корневой Logger.
        """
        return LoggerConfig.setup_logger(
            "valutatrade_hub",
            level=level,
            console_level=console_level,
            file_level=file_level,
            use_file=True
        )


# Глобальная инициализация логирования
def initialize_logging(
    level: int = logging.INFO,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Инициализирует систему логирования приложения.
    
    Должна быть вызвана один раз в main.py перед использованием логеров.
    
    Args:
        level: Общий уровень логирования.
        console_level: Уровень для консоли.
        file_level: Уровень для файла.
        
    Returns:
        Корневой логер приложения.
        
    Example:
        >>> logger = initialize_logging()
        >>> logger.info("Application started")
    """
    logger = LoggerConfig.setup_root_logger(
        level=level,
        console_level=console_level,
        file_level=file_level
    )
    
    logger.info("=" * 70)
    logger.info(f"Logging initialized at {datetime.utcnow().isoformat()}")
    logger.info(f"Log file: {LoggerConfig.LOG_FILE}")
    logger.info("=" * 70)
    
    return logger


# Удобная функция для получения логера в модулях
def get_logger(module_name: str) -> logging.Logger:
    """
    Быстро получить логер для конкретного модуля.
    
    Args:
        module_name: Имя модуля (обычно __name__).
        
    Returns:
        Объект Logger для модуля.
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    """
    return logging.getLogger(f"valutatrade_hub.{module_name}")


# Вспомогательный класс для контекстного логирования операций
class LogContext:
    """
    Контекстный менеджер для логирования начала и конца операций.
    
    Использование:
        >>> logger = get_logger(__name__)
        >>> with LogContext(logger, "Database query"):
        ...     # выполнить запрос
        ...     pass
    """
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        Инициализация контекста логирования.
        
        Args:
            logger: Логер для использования.
            operation: Описание операции.
        """
        self.logger = logger
        self.operation = operation
    
    def __enter__(self):
        """Логирует начало операции."""
        self.logger.debug(f"▶ Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Логирует конец операции или ошибку."""
        if exc_type is None:
            self.logger.debug(f"✓ Completed: {self.operation}")
        else:
            self.logger.error(
                f"✗ Failed: {self.operation} - {exc_type.__name__}: {exc_val}"
            )
        return False  # Не подавляем исключения

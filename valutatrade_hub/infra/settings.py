"""
Модуль конфигурации приложения (Singleton паттерн).
Загружает и управляет глобальными настройками приложения.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.core.exceptions import SettingsError


class SettingsLoader:
    """
    Singleton класс для загрузки и управления настройками приложения.
    
    Загружает конфигурацию из JSON файла и предоставляет доступ к настройкам.
    """
    
    # Singleton instance
    _instance: Optional["SettingsLoader"] = None
    
    # Пути к файлам конфигурации
    CONFIG_DIR = Path("config")
    DEFAULT_CONFIG_FILE = CONFIG_DIR / "settings.json"
    
    # Стандартные значения
    DEFAULT_SETTINGS = {
        "app": {
            "name": "ValutaTrade Hub",
            "version": "0.1.0",
            "environment": "development",
        },
        "database": {
            "users_file": "data/users.json",
            "portfolios_file": "data/portfolios.json",
            "rates_file": "data/exchange_rates.json",
        },
        "api": {
            "default_timeout": 10,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
        "logging": {
            "level": "INFO",
            "console_level": "INFO",
            "file_level": "DEBUG",
        },
        "features": {
            "enable_api": True,
            "enable_parser": True,
            "cache_rates": True,
        },
    }
    
    def __new__(cls) -> "SettingsLoader":
        """Реализация Singleton паттерна."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Инициализация SettingsLoader.
        
        Загружает конфигурацию из файла или использует стандартные значения.
        """
        if self._initialized:
            return
        
        self.logger = get_logger(__name__)
        self._settings: Dict[str, Any] = self.DEFAULT_SETTINGS.copy()
        self._config_file = self.DEFAULT_CONFIG_FILE
        
        # Пытаемся загрузить конфигурацию из файла
        self._load_config()
        
        self.logger.info(f"Settings loaded from {self._config_file}")
        self._initialized = True
    
    def _load_config(self) -> None:
        """
        Загружает конфигурацию из JSON файла.
        
        Если файл не существует, использует стандартные значения
        и создаёт файл конфигурации.
        
        Raises:
            SettingsError: Если файл повреждён.
        """
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    # Объединяем с дефолтными значениями
                    self._merge_settings(config_data)
                    self.logger.debug(f"Config loaded from {self._config_file}")
            except json.JSONDecodeError as e:
                raise SettingsError(
                    f"Config file {self._config_file} is corrupted: {e}"
                )
            except Exception as e:
                raise SettingsError(f"Failed to load config: {e}")
        else:
            self.logger.info(
                f"Config file not found at {self._config_file}. "
                "Using default settings."
            )
            self._save_config()
    
    def _merge_settings(self, loaded_config: Dict[str, Any]) -> None:
        """
        Объединяет загруженные настройки с дефолтными.
        
        Загруженные значения переопределяют дефолтные.
        
        Args:
            loaded_config: Загруженная конфигурация.
        """
        for section, values in loaded_config.items():
            if section in self._settings and isinstance(values, dict):
                self._settings[section].update(values)
            else:
                self._settings[section] = values
    
    def _save_config(self) -> None:
        """
        Сохраняет текущие настройки в JSON файл.
        
        Создаёт директорию, если её нет.
        """
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Config saved to {self._config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение настройки по ключу (dot-notation поддерживается).
        
        Примеры:
            >>> settings.get("app.name")
            "ValutaTrade Hub"
            >>> settings.get("database.users_file")
            "data/users.json"
            >>> settings.get("nonexistent", "default_value")
            "default_value"
        
        Args:
            key: Ключ настройки (может содержать точки для вложенных ключей).
            default: Значение по умолчанию, если ключ не найден.
            
        Returns:
            Значение настройки или default.
        """
        keys = key.split(".")
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Устанавливает значение настройки (dot-notation поддерживается).
        
        Примеры:
            >>> settings.set("app.name", "New Name")
            >>> settings.set("database.users_file", "new_path.json")
        
        Args:
            key: Ключ настройки (может содержать точки).
            value: Новое значение.
        """
        keys = key.split(".")
        current = self._settings
        
        # Навигируемся к родительскому объекту
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Устанавливаем значение
        current[keys[-1]] = value
        self.logger.debug(f"Setting {key} = {value}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Получает целую секцию настроек.
        
        Args:
            section: Название секции (например, "database", "api").
            
        Returns:
            Словарь с настройками секции или пустой словарь.
        """
        return self._settings.get(section, {}).copy()
    
    def get_all(self) -> Dict[str, Any]:
        """Возвращает копию всех настроек."""
        return self._settings.copy()
    
    def reload(self, config_file: Optional[Path] = None) -> None:
        """
        Перезагружает конфигурацию из файла.
        
        Args:
            config_file: Путь к новому файлу конфигурации (опционально).
        """
        if config_file:
            self._config_file = config_file
        
        self._settings = self.DEFAULT_SETTINGS.copy()
        self._load_config()
        self.logger.info("Settings reloaded")
    
    def validate(self) -> bool:
        """
        Валидирует текущие настройки.
        
        Returns:
            True если настройки корректны, иначе False.
        """
        required_sections = ["app", "database", "api", "logging"]
        
        for section in required_sections:
            if section not in self._settings:
                self.logger.error(f"Required section '{section}' is missing")
                return False
        
        return True
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return f"SettingsLoader(config={self._config_file})"


# Глобальный экземпляр SettingsLoader
_GLOBAL_SETTINGS: Optional[SettingsLoader] = None


def get_settings() -> SettingsLoader:
    """
    Получает глобальный экземпляр SettingsLoader (Singleton).
    
    Returns:
        Глобальный объект SettingsLoader.
        
    Example:
        >>> settings = get_settings()
        >>> db_file = settings.get("database.users_file")
    """
    global _GLOBAL_SETTINGS
    if _GLOBAL_SETTINGS is None:
        _GLOBAL_SETTINGS = SettingsLoader()
    return _GLOBAL_SETTINGS


def reset_settings() -> None:
    """
    Сбрасывает глобальный экземпляр SettingsLoader (для тестирования).
    """
    global _GLOBAL_SETTINGS
    _GLOBAL_SETTINGS = None

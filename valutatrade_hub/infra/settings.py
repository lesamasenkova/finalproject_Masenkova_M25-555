"""Singleton для управления настройками приложения."""

import json
import os
from typing import Any, Optional


class SettingsLoader:
    """Singleton для загрузки и кеширования конфигурации."""

    _instance: Optional["SettingsLoader"] = None
    _config: dict = {}

    def __new__(cls):
        """Реализация Singleton через __new__."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Загрузить конфигурацию из файла или использовать значения по умолчанию."""
        # Значения по умолчанию
        self._config = {
            "data_dir": "data",
            "logs_dir": "logs",
            "users_file": "data/users.json",
            "portfolios_file": "data/portfolios.json",
            "rates_file": "data/rates.json",
            "rates_ttl_seconds": 300,  # 5 минут
            "default_base_currency": "USD",
            "log_level": "INFO",
            "max_log_size_mb": 10,
            "log_backup_count": 5,
        }

        # Попытка загрузить из config.json (если существует)
        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self._config.update(user_config)
            except Exception as e:
                print(f"Предупреждение: не удалось загрузить {config_file}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение настройки.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или default
        """
        return self._config.get(key, default)

    def reload(self):
        """Перезагрузить конфигурацию из файла."""
        self._load_config()

    def get_all(self) -> dict:
        """Получить все настройки."""
        return self._config.copy()


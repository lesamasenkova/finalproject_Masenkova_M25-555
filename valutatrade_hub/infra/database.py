"""Singleton для управления доступом к данным."""

import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, List, Optional

from valutatrade_hub.core.exceptions import ValidationError
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Singleton для управления JSON-хранилищем."""

    _instance: Optional["DatabaseManager"] = None
    _settings: Optional[SettingsLoader] = None 

    def __new__(cls):
        """Реализация Singleton через __new__."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = SettingsLoader()
        return cls._instance

    def _ensure_file_exists(self, filepath: str, default_content: Any):
        """Убедиться, что файл существует."""
        if not os.path.exists(filepath):
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)

    def _save_json_atomic(self, filepath: str, data: Any):
        """
        Атомарно сохранить JSON в файл.

        Args:
            filepath: Путь к файлу
            data: Данные для сохранения
        """
        directory = os.path.dirname(filepath) or "."
        temp_fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            shutil.move(temp_path, filepath)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def load_users(self) -> List[User]:
        """Загрузить пользователей."""
        filepath = self._settings.get("users_file")
        self._ensure_file_exists(filepath, [])

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                users_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Файл {filepath} содержит невалидный JSON: {e}")
        except FileNotFoundError:
            return []

        users = []
        for data in users_data:
            try:
                # Проверка обязательных полей
                required_fields = [
                    "user_id",
                    "username",
                    "hashed_password",
                    "salt",
                    "registration_date",
                ]
                missing = [f for f in required_fields if f not in data]
                if missing:
                    print(f"Предупреждение: пропуск записи, отсутствуют поля: {missing}")
                    continue

                user = User(
                    user_id=data["user_id"],
                    username=data["username"],
                    hashed_password=data["hashed_password"],
                    salt=data["salt"],
                    registration_date=datetime.fromisoformat(data["registration_date"]),
                )
                users.append(user)
            except (KeyError, ValueError) as e:
                print(f"Предупреждение: пропуск поврежденной записи пользователя: {e}")

        return users

    def save_users(self, users: List[User]):
        """Сохранить пользователей."""
        filepath = self._settings.get("users_file")
        users_data = [
            {
                "user_id": u.user_id,
                "username": u.username,
                "hashed_password": u.hashed_password,
                "salt": u.salt,
                "registration_date": u.registration_date.isoformat(),
            }
            for u in users
        ]
        with open(filepath, "w", encoding="utf-8") as f:  
            json.dump(users_data, f, ensure_ascii=False, indent=2)
            f.flush() 
            os.fsync(f.fileno())
            
    def load_portfolios(self) -> List[Portfolio]:
        """Загрузить портфели."""
        filepath = self._settings.get("portfolios_file")
        self._ensure_file_exists(filepath, [])

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                portfolios_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Файл {filepath} содержит невалидный JSON: {e}")
        except FileNotFoundError:
            return []

        portfolios = []
        for data in portfolios_data:
            try:
                wallets = {}
                for code, wallet_data in data.get("wallets", {}).items():
                    wallets[code] = Wallet(code, wallet_data.get("balance", 0.0))
                portfolio = Portfolio(data["user_id"], wallets)
                portfolios.append(portfolio)
            except (KeyError, ValueError) as e:
                print(f"Предупреждение: пропуск поврежденного портфеля: {e}")

        return portfolios

    def save_portfolios(self, portfolios: List[Portfolio]):
        """Сохранить портфели."""
        filepath = self._settings.get("portfolios_file")
        portfolios_data = [p.to_dict() for p in portfolios]
        self._save_json_atomic(filepath, portfolios_data)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(portfolios_data, f, ensure_ascii=False, indent=2)
            f.flush() 
            os.fsync(f.fileno())  
            
    def load_rates(self) -> dict:
        """Загрузить курсы валют."""
        filepath = self._settings.get("rates_file")
        self._ensure_file_exists(filepath, {})

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Предупреждение: невалидный JSON в {filepath}: {e}")
            return {}
        except FileNotFoundError:
            return {}

    def save_rates(self, rates: dict):
        """Сохранить курсы валют."""
        filepath = self._settings.get("rates_file")
        self._save_json_atomic(filepath, rates)


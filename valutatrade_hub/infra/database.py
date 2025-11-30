"""
Модуль управления базой данных (Singleton паттерн).
Управляет загрузкой, сохранением и синхронизацией данных в JSON файлы.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.core.exceptions import DatabaseError
from valutatrade_hub.core.models import User, Portfolio
from valutatrade_hub.infra.settings import get_settings


class DatabaseManager:
    """
    Singleton класс для управления данными приложения.
    
    Загружает и сохраняет пользователей, портфели и курсы валют в JSON файлы.
    Обеспечивает синхронизацию данных между памятью и диском.
    """
    
    # Singleton instance
    _instance: Optional["DatabaseManager"] = None
    
    def __new__(cls) -> "DatabaseManager":
        """Реализация Singleton паттерна."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Инициализация DatabaseManager.
        
        Загружает настройки и инициализирует хранилище данных.
        """
        if self._initialized:
            return
        
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        
        # Получаем пути из настроек
        self.data_dir = Path(self.settings.get("database.users_file")).parent
        self.users_file = Path(self.settings.get("database.users_file"))
        self.portfolios_file = Path(self.settings.get("database.portfolios_file"))
        self.rates_file = Path(self.settings.get("database.rates_file"))
        
        # Создаём директорию данных, если её нет
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализируем хранилище в памяти
        self._users: Dict[str, User] = {}  # username -> User
        self._portfolios: Dict[int, Portfolio] = {}  # user_id -> Portfolio
        self._exchange_rates: Dict[str, float] = {}  # pair -> rate
        
        # Загружаем данные из файлов
        self._load_data()
        
        self.logger.info("Database initialized")
        self._initialized = True
    
    def _load_data(self) -> None:
        """
        Загружает все данные из JSON файлов.
        
        Если файлы не существуют, создаёт пустые хранилища.
        """
        self._load_users()
        self._load_portfolios()
        self._load_exchange_rates()
    
    def _load_users(self) -> None:
        """Загружает пользователей из JSON файла."""
        try:
            if self.users_file.exists():
                with open(self.users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        user = User.from_dict(user_data)
                        self._users[username] = user
                self.logger.debug(f"Loaded {len(self._users)} users")
            else:
                self.logger.debug("Users file not found, starting with empty database")
                self._save_users()
        except Exception as e:
            raise DatabaseError(f"Failed to load users: {e}")
    
    def _load_portfolios(self) -> None:
        """Загружает портфели из JSON файла."""
        try:
            if self.portfolios_file.exists():
                with open(self.portfolios_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id_str, portfolio_data in data.items():
                        user_id = int(user_id_str)
                        portfolio = Portfolio.from_dict(portfolio_data)
                        self._portfolios[user_id] = portfolio
                self.logger.debug(f"Loaded {len(self._portfolios)} portfolios")
            else:
                self.logger.debug("Portfolios file not found, starting with empty database")
                self._save_portfolios()
        except Exception as e:
            raise DatabaseError(f"Failed to load portfolios: {e}")
    
    def _load_exchange_rates(self) -> None:
        """Загружает курсы валют из JSON файла."""
        try:
            if self.rates_file.exists():
                with open(self.rates_file, "r", encoding="utf-8") as f:
                    self._exchange_rates = json.load(f)
                self.logger.debug(f"Loaded {len(self._exchange_rates)} exchange rates")
            else:
                self.logger.debug("Rates file not found, starting with empty rates")
                # Используем дефолтные курсы из Portfolio
                from valutatrade_hub.core.models import Portfolio
                self._exchange_rates = Portfolio._get_default_rates()
                self._save_exchange_rates()
        except Exception as e:
            raise DatabaseError(f"Failed to load exchange rates: {e}")
    
    def _save_users(self) -> None:
        """Сохраняет пользователей в JSON файл."""
        try:
            data = {username: user.to_dict() for username, user in self._users.items()}
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Saved {len(self._users)} users")
        except Exception as e:
            self.logger.error(f"Failed to save users: {e}")
            raise DatabaseError(f"Failed to save users: {e}")
    
    def _save_portfolios(self) -> None:
        """Сохраняет портфели в JSON файл."""
        try:
            data = {str(user_id): portfolio.to_dict() 
                    for user_id, portfolio in self._portfolios.items()}
            with open(self.portfolios_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Saved {len(self._portfolios)} portfolios")
        except Exception as e:
            self.logger.error(f"Failed to save portfolios: {e}")
            raise DatabaseError(f"Failed to save portfolios: {e}")
    
    def _save_exchange_rates(self) -> None:
        """Сохраняет курсы валют в JSON файл."""
        try:
            with open(self.rates_file, "w", encoding="utf-8") as f:
                json.dump(self._exchange_rates, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Saved {len(self._exchange_rates)} exchange rates")
        except Exception as e:
            self.logger.error(f"Failed to save exchange rates: {e}")
            raise DatabaseError(f"Failed to save exchange rates: {e}")
    
    # ============= Методы работы с пользователями =============
    
    def add_user(self, user: User) -> None:
        """
        Добавляет пользователя в базу данных.
        
        Args:
            user: Объект User для добавления.
        """
        self._users[user.username] = user
        self._save_users()
        self.logger.info(f"User '{user.username}' added to database")
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Получает пользователя по имени.
        
        Args:
            username: Имя пользователя.
            
        Returns:
            Объект User или None если не найден.
        """
        return self._users.get(username)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по ID.
        
        Args:
            user_id: ID пользователя.
            
        Returns:
            Объект User или None если не найден.
        """
        for user in self._users.values():
            if user.user_id == user_id:
                return user
        return None
    
    def user_exists(self, username: str) -> bool:
        """Проверяет, существует ли пользователь."""
        return username in self._users
    
    def get_all_users(self) -> Dict[str, User]:
        """Возвращает копию словаря всех пользователей."""
        return self._users.copy()
    
    def update_user(self, user: User) -> None:
        """
        Обновляет данные пользователя.
        
        Args:
            user: Обновлённый объект User.
        """
        if user.username not in self._users:
            raise DatabaseError(f"User '{user.username}' not found")
        
        self._users[user.username] = user
        self._save_users()
        self.logger.info(f"User '{user.username}' updated")
    
    def delete_user(self, username: str) -> None:
        """
        Удаляет пользователя из базы данных.
        
        Args:
            username: Имя пользователя.
        """
        if username not in self._users:
            raise DatabaseError(f"User '{username}' not found")
        
        user = self._users.pop(username)
        
        # Удаляем портфель пользователя
        if user.user_id in self._portfolios:
            del self._portfolios[user.user_id]
            self._save_portfolios()
        
        self._save_users()
        self.logger.info(f"User '{username}' deleted")
    
    # ============= Методы работы с портфелями =============
    
    def add_portfolio(self, portfolio: Portfolio) -> None:
        """
        Добавляет портфель в базу данных.
        
        Args:
            portfolio: Объект Portfolio для добавления.
        """
        self._portfolios[portfolio.user_id] = portfolio
        self._save_portfolios()
        self.logger.info(f"Portfolio for user {portfolio.user_id} added")
    
    def get_portfolio(self, user_id: int) -> Optional[Portfolio]:
        """
        Получает портфель по ID пользователя.
        
        Args:
            user_id: ID пользователя.
            
        Returns:
            Объект Portfolio или None если не найден.
        """
        return self._portfolios.get(user_id)
    
    def update_portfolio(self, portfolio: Portfolio) -> None:
        """
        Обновляет портфель в базе данных.
        
        Args:
            portfolio: Обновлённый объект Portfolio.
        """
        if portfolio.user_id not in self._portfolios:
            raise DatabaseError(f"Portfolio for user {portfolio.user_id} not found")
        
        self._portfolios[portfolio.user_id] = portfolio
        self._save_portfolios()
        self.logger.info(f"Portfolio for user {portfolio.user_id} updated")
    
    # ============= Методы работы с курсами валют =============
    
    def set_exchange_rate(self, from_code: str, to_code: str, rate: float) -> None:
        """
        Устанавливает курс обмена между двумя валютами.
        
        Args:
            from_code: Исходная валюта.
            to_code: Целевая валюта.
            rate: Курс обмена.
        """
        pair_key = f"{from_code.upper()}_{to_code.upper()}"
        self._exchange_rates[pair_key] = float(rate)
        self._save_exchange_rates()
        self.logger.debug(f"Exchange rate {pair_key} = {rate}")
    
    def get_exchange_rate(self, from_code: str, to_code: str) -> Optional[float]:
        """
        Получает курс обмена между двумя валютами.
        
        Args:
            from_code: Исходная валюта.
            to_code: Целевая валюта.
            
        Returns:
            Курс обмена или None если не найден.
        """
        pair_key = f"{from_code.upper()}_{to_code.upper()}"
        return self._exchange_rates.get(pair_key)
    
    def get_all_exchange_rates(self) -> Dict[str, float]:
        """Возвращает копию словаря всех курсов валют."""
        return self._exchange_rates.copy()
    
    def update_exchange_rates(self, rates: Dict[str, float]) -> None:
        """
        Обновляет несколько курсов валют одновременно.
        
        Args:
            rates: Словарь курсов вида {"USD_EUR": 0.927, ...}.
        """
        self._exchange_rates.update(rates)
        self._save_exchange_rates()
        self.logger.info(f"Updated {len(rates)} exchange rates")
    
    # ============= Синхронизация =============
    
    def sync(self) -> None:
        """
        Синхронизирует все данные с диском (сохраняет всё).
        
        Используется при критических операциях.
        """
        self._save_users()
        self._save_portfolios()
        self._save_exchange_rates()
        self.logger.info("Database synchronized with disk")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по базе данных.
        
        Returns:
            Словарь со статистикой.
        """
        return {
            "users_count": len(self._users),
            "portfolios_count": len(self._portfolios),
            "exchange_rates_count": len(self._exchange_rates),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return (
            f"DatabaseManager("
            f"users={len(self._users)}, "
            f"portfolios={len(self._portfolios)}, "
            f"rates={len(self._exchange_rates)}"
            f")"
        )


# Глобальный экземпляр DatabaseManager
_GLOBAL_DB: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """
    Получает глобальный экземпляр DatabaseManager (Singleton).
    
    Returns:
        Глобальный объект DatabaseManager.
        
    Example:
        >>> db = get_database()
        >>> user = db.get_user("alice")
    """
    global _GLOBAL_DB
    if _GLOBAL_DB is None:
        _GLOBAL_DB = DatabaseManager()
    return _GLOBAL_DB


def reset_database() -> None:
    """
    Сбрасывает глобальный экземпляр DatabaseManager (для тестирования).
    """
    global _GLOBAL_DB
    _GLOBAL_DB = None

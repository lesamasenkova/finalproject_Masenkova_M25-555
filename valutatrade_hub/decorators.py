"""
Модуль пользовательских декораторов для приложения.
Содержит декоратор @log_action для логирования вызовов функций.
"""
import functools
import time
from typing import Callable, Any

from valutatrade_hub.logging_config import get_logger


def log_action(func: Callable) -> Callable:
    """
    Декоратор для автоматического логирования вызовов функций.
    
    Логирует:
    - Имя функции и модуля
    - Переданные аргументы (без конфиденциальных данных)
    - Результат выполнения или ошибку
    - Время выполнения
    
    Пример использования:
        >>> @log_action
        ... def buy_currency(amount: float, currency: str) -> bool:
        ...     # Логика покупки
        ...     return True
        
    Args:
        func: Функция для декорирования.
        
    Returns:
        Оборнутая функция с логированием.
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        """
        Оборнутая функция с логированием.
        
        Args:
            *args: Позиционные аргументы для func.
            **kwargs: Именованные аргументы для func.
            
        Returns:
            Результат выполнения func.
        """
        # Получаем логер
        logger = get_logger(func.__module__)
        
        # Подготавливаем информацию о вызове
        func_name = func.__qualname__  # Учитывает вложенные функции и методы
        
        # Форматируем аргументы (скрываем конфиденциальные данные)
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={_sanitize_value(k, v)}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        
        # Логируем начало выполнения
        logger.debug(f"→ Calling {func_name}({signature})")
        
        # Засекаем время
        start_time = time.time()
        
        try:
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Засекаем время выполнения
            elapsed_time = time.time() - start_time
            
            # Логируем успешное завершение
            result_repr = _format_result(result)
            logger.debug(
                f"← Completed {func_name}() "
                f"→ {result_repr} "
                f"[{elapsed_time:.4f}s]"
            )
            
            return result
        
        except Exception as exc:
            # Засекаем время выполнения до ошибки
            elapsed_time = time.time() - start_time
            
            # Логируем ошибку
            logger.error(
                f"✗ Failed {func_name}() "
                f"with {exc.__class__.__name__}: {exc} "
                f"[{elapsed_time:.4f}s]"
            )
            
            # Пробрасываем исключение дальше
            raise
    
    return wrapper


def log_method(func: Callable) -> Callable:
    """
    Декоратор для логирования методов класса.
    
    Вариант @log_action, специально оптимизированный для методов.
    Использует self.__class__.__name__ для более информативных логов.
    
    Пример использования:
        >>> class Portfolio:
        ...     @log_method
        ...     def add_currency(self, code: str) -> None:
        ...         # Логика добавления
        ...         pass
    
    Args:
        func: Метод для декорирования.
        
    Returns:
        Оборнутый метод с логированием.
    """
    
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        """
        Оборнутый метод с логированием.
        
        Args:
            self: Экземпляр класса.
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
            
        Returns:
            Результат выполнения func.
        """
        logger = get_logger(func.__module__)
        
        # Форматируем имя для логов: ClassName.method_name
        class_name = self.__class__.__name__
        func_name = func.__qualname__.split(".")[-1]  # Берём последнюю часть
        full_name = f"{class_name}.{func_name}"
        
        # Форматируем аргументы
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={_sanitize_value(k, v)}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        
        logger.debug(f"→ Calling {full_name}({signature})")
        
        start_time = time.time()
        
        try:
            result = func(self, *args, **kwargs)
            elapsed_time = time.time() - start_time
            
            result_repr = _format_result(result)
            logger.debug(
                f"← Completed {full_name}() "
                f"→ {result_repr} "
                f"[{elapsed_time:.4f}s]"
            )
            
            return result
        
        except Exception as exc:
            elapsed_time = time.time() - start_time
            
            logger.error(
                f"✗ Failed {full_name}() "
                f"with {exc.__class__.__name__}: {exc} "
                f"[{elapsed_time:.4f}s]"
            )
            
            raise
    
    return wrapper


# ============= Вспомогательные функции =============

def _sanitize_value(key: str, value: Any, max_length: int = 50) -> str:
    """
    Санитизирует значение для логирования (скрывает конфиденциальные данные).
    
    Скрывает:
    - Пароли (если ключ содержит "password")
    - Токены и ключи
    - Хешированные значения
    - Очень длинные строки
    
    Args:
        key: Имя переменной (для определения типа).
        value: Значение для санитизации.
        max_length: Максимальная длина для отображения.
        
    Returns:
        Санитизированное строковое представление.
    """
    # Скрываем пароли
    if "password" in key.lower() or "secret" in key.lower():
        return "***REDACTED***"
    
    # Скрываем токены и ключи
    if "token" in key.lower() or "key" in key.lower():
        return "***REDACTED***"
    
    # Обрезаем слишком длинные строки
    value_str = repr(value)
    if len(value_str) > max_length:
        return value_str[:max_length] + "..."
    
    return value_str


def _format_result(result: Any, max_length: int = 50) -> str:
    """
    Форматирует результат функции для логирования.
    
    Args:
        result: Результат функции.
        max_length: Максимальная длина для отображения.
        
    Returns:
        Отформатированное строковое представление.
    """
    # Обрабатываем None
    if result is None:
        return "None"
    
    # Обрабатываем булевы значения
    if isinstance(result, bool):
        return "✓ True" if result else "✗ False"
    
    # Обрабатываем числа
    if isinstance(result, (int, float)):
        return f"{result}"
    
    # Обрабатываем словари
    if isinstance(result, dict):
        keys_count = len(result)
        return f"dict({keys_count} keys)"
    
    # Обрабатываем списки и кортежи
    if isinstance(result, (list, tuple)):
        items_count = len(result)
        type_name = type(result).__name__
        return f"{type_name}({items_count} items)"
    
    # Обрабатываем строки
    if isinstance(result, str):
        if len(result) > max_length:
            return f'"{result[:max_length]}..."'
        return f'"{result}"'
    
    # Для остального — используем repr
    result_str = repr(result)
    if len(result_str) > max_length:
        return result_str[:max_length] + "..."
    
    return result_str


def catch_and_log(func: Callable) -> Callable:
    """
    Декоратор для ловки исключений с логированием (без пробрасывания).
    
    Используется для функций, которые должны работать несмотря на ошибки.
    Логирует ошибку, но не пробрасывает исключение дальше.
    
    Пример использования:
        >>> @catch_and_log
        ... def optional_operation() -> bool:
        ...     # Может вызвать ошибку, но программа продолжит работу
        ...     return True
    
    Args:
        func: Функция для декорирования.
        
    Returns:
        Оборнутая функция с обработкой исключений.
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        """
        Оборнутая функция с обработкой исключений.
        
        Args:
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
            
        Returns:
            Результат выполнения func или None если произошла ошибка.
        """
        logger = get_logger(func.__module__)
        
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.warning(
                f"Caught exception in {func.__qualname__}: "
                f"{exc.__class__.__name__}: {exc}"
            )
            return None
    
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """
    Декоратор для повторных попыток выполнения функции при ошибке.
    
    Пример использования:
        >>> @retry(max_attempts=3, delay=2.0)
        ... def fetch_from_api() -> dict:
        ...     # Может временно не работать
        ...     return api.get_data()
    
    Args:
        max_attempts: Максимальное количество попыток.
        delay: Задержка между попытками (в секундах).
        
    Returns:
        Декоратор для применения к функции.
    """
    
    def decorator(func: Callable) -> Callable:
        """Внутренний декоратор."""
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """Оборнутая функция с повторными попытками."""
            logger = get_logger(func.__module__)
            
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed "
                            f"for {func.__qualname__}: {exc}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed "
                            f"for {func.__qualname__}: {exc}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


def time_it(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения функции.
    
    Логирует время выполнения на уровне INFO.
    
    Пример использования:
        >>> @time_it
        ... def slow_operation():
        ...     # Долгая операция
        ...     time.sleep(2)
    
    Args:
        func: Функция для декорирования.
        
    Returns:
        Оборнутая функция с измерением времени.
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        """Оборнутая функция с измерением времени."""
        logger = get_logger(func.__module__)
        
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # Выбираем уровень логирования в зависимости от времени
        if elapsed_time > 5.0:
            log_level = logger.warning
            status = "⚠ SLOW"
        elif elapsed_time > 1.0:
            log_level = logger.info
            status = "⏱ MODERATE"
        else:
            log_level = logger.debug
            status = "✓ FAST"
        
        log_level(
            f"{status} {func.__qualname__} completed in {elapsed_time:.4f}s"
        )
        
        return result
    
    return wrapper

"""Декораторы для логирования операций."""

import functools
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.
    
    Args:
        action_name: Название операции (BUY, SELL, REGISTER, LOGIN)
        verbose: Добавлять ли подробный контекст
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Подготовка контекста для логирования
            timestamp = datetime.now().isoformat()
            
            # Извлекаем параметры из args/kwargs
            context = {
                "action": action_name,
                "timestamp": timestamp,
                "function": func.__name__,
            }
            
            # Пытаемся извлечь username, currency, amount из аргументов
            if len(args) > 0 and hasattr(args[0], "username"):
                context["user"] = args[0].username
            
            if "currency" in kwargs:
                context["currency"] = kwargs["currency"]
            elif len(args) > 1:
                context["currency"] = args[1] if isinstance(args[1], str) else None
            
            if "amount" in kwargs:
                context["amount"] = kwargs["amount"]
            elif len(args) > 2:
                context["amount"] = args[2] if isinstance(args[2], (int, float)) else None

            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем успех
                log_message = f"{action_name}"
                if "user" in context:
                    log_message += f" user='{context['user']}'"
                if "currency" in context and context["currency"]:
                    log_message += f" currency='{context['currency']}'"
                if "amount" in context and context["amount"]:
                    log_message += f" amount={context['amount']}"
                log_message += " result=OK"
                
                logger.info(log_message)
                
                return result
                
            except Exception as e:
                # Логируем ошибку
                error_type = type(e).__name__
                error_message = str(e)
                
                log_message = f"{action_name}"
                if "user" in context:
                    log_message += f" user='{context['user']}'"
                if "currency" in context and context["currency"]:
                    log_message += f" currency='{context['currency']}'"
                if "amount" in context and context["amount"]:
                    log_message += f" amount={context['amount']}"
                log_message += f" result=ERROR error_type={error_type} error_message='{error_message}'"
                
                logger.error(log_message)
                
                # Пробрасываем исключение дальше
                raise

        return wrapper

    return decorator


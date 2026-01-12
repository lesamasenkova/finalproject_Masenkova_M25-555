"""Декораторы для логирования операций."""

import functools
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def log_action(action_name: str): 
    """
    Декоратор для логирования доменных операций.

    Args:
        action_name: Название операции (BUY, SELL, REGISTER, LOGIN)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Подготовка контекста для логирования
            timestamp = datetime.now().isoformat()

            context = {
                "action": action_name,
                "timestamp": timestamp,
                "function": func.__name__,
            }

            
            # Для classmethod: args[0] = cls, для обычных методов: args[0] = self
            if "username" in kwargs:
                context["user"] = kwargs["username"]
            elif len(args) > 1 and isinstance(args[1], str):
                # Вероятно, username - первый аргумент после cls/self
                context["user"] = args[1]

            if "currency" in kwargs:
                context["currency"] = kwargs["currency"]
            elif len(args) > 1:
                # Пытаемся найти currency в позиционных аргументах
                for arg in args[1:]:
                    if isinstance(arg, str) and arg.isupper() and 2 <= len(arg) <= 5:
                        context["currency"] = arg
                        break

            if "amount" in kwargs:
                context["amount"] = kwargs["amount"]
            elif len(args) > 2:
                for arg in args[2:]:
                    if isinstance(arg, (int, float)):
                        context["amount"] = arg
                        break

            try:
                # Выполняем функцию
                result = func(*args, **kwargs)

                # Логируем успех
                log_message = f"{action_name}"
                if "user" in context:
                    log_message += f" user='{context['user']}'"
                if "currency" in context:
                    log_message += f" currency='{context['currency']}'"
                if "amount" in context:
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
                if "currency" in context:
                    log_message += f" currency='{context['currency']}'"
                if "amount" in context:
                    log_message += f" amount={context['amount']}"
                log_message += f" result=ERROR error_type={error_type} error_message='{error_message}'"

                logger.error(log_message)

                # Пробрасываем исключение дальше
                raise

        return wrapper

    return decorator


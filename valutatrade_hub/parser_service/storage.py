"""Хранилище данных для Parser Service."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class RatesStorage:
    """Класс для работы с хранилищем курсов."""

    def __init__(self, rates_file: str, history_file: str):
        """
        Инициализация хранилища.
        
        Args:
            rates_file: Путь к файлу с текущими курсами (rates.json)
            history_file: Путь к файлу с историей (exchange_rates.json)
        """
        self.rates_file = rates_file
        self.history_file = history_file

    def save_current_rates(self, rates: Dict[str, float], source_map: Dict[str, str]):
        """
        Сохранить текущие курсы в rates.json.
        
        Args:
            rates: Словарь {пара: курс}
            source_map: Словарь {пара: источник}
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Формируем структуру для rates.json
        data = {"pairs": {}, "last_refresh": timestamp}

        for pair, rate in rates.items():
            data["pairs"][pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": source_map.get(pair, "Unknown"),
            }

        # Атомарная запись через временный файл
        temp_file = self.rates_file + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.rates_file)
            logger.info(f"Saved {len(rates)} rates to {self.rates_file}")
        except Exception as e:
            logger.error(f"Failed to save rates: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

    def append_to_history(self, rates: Dict[str, float], source_map: Dict[str, str]):
        """
        Добавить записи в историю exchange_rates.json.
        
        Args:
            rates: Словарь {пара: курс}
            source_map: Словарь {пара: источник}
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Загружаем существующую историю
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")

        # Добавляем новые записи
        for pair, rate in rates.items():
            from_curr, to_curr = pair.split("_")
            record = {
                "id": f"{pair}_{timestamp}",
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": rate,
                "timestamp": timestamp,
                "source": source_map.get(pair, "Unknown"),
            }
            history.append(record)

        # Сохраняем
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"Appended {len(rates)} records to history")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            raise

    def load_current_rates(self) -> Dict[str, float]:
        """
        Загрузить текущие курсы из rates.json.
        
        Returns:
            Словарь {пара: курс}
        """
        if not os.path.exists(self.rates_file):
            return {}

        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pairs = data.get("pairs", {})
            return {pair: info["rate"] for pair, info in pairs.items()}
        except Exception as e:
            logger.error(f"Failed to load rates: {e}")
            return {}


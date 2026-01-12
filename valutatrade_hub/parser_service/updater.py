"""Координатор обновления курсов валют."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional 

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger(__name__)


class RatesUpdater:
    """Класс для координации обновления курсов."""

    def __init__(self, clients: List[BaseApiClient], storage: RatesStorage):
        """
        Инициализация updater.

        Args:
            clients: Список API клиентов
            storage: Хранилище данных
        """
        self.clients = clients
        self.storage = storage

    def run_update(self, source_filter: Optional[str] = None) -> Dict[str, Any]: 
        """
        Запустить обновление курсов.

        Args:
            source_filter: Фильтр по источнику ('coingecko', 'exchangerate' или None для всех)

        Returns:
            Словарь со статистикой обновления
        """
        logger.info("=" * 60)
        logger.info("Starting rates update...")
        logger.info("=" * 60)

        all_rates = {}
        source_map = {}  # Отслеживаем источник для каждой пары
        errors = []
        successful_sources = []

        for client in self.clients:
            client_name = client.__class__.__name__

            # Применяем фильтр по источнику
            if source_filter:
                if (
                    source_filter.lower() == "coingecko"
                    and "CoinGecko" not in client_name
                ):
                    continue
                if (
                    source_filter.lower() == "exchangerate"
                    and "ExchangeRate" not in client_name
                ):
                    continue

            try:
                logger.info(f"Fetching from {client_name}...")
                rates = client.fetch_rates()

                # Определяем источник
                if "CoinGecko" in client_name:
                    source = "CoinGecko"
                elif "ExchangeRate" in client_name:
                    source = "ExchangeRate-API"
                else:
                    source = "Unknown"

                # Добавляем курсы
                for pair, rate in rates.items():
                    all_rates[pair] = rate
                    source_map[pair] = source

                logger.info(f"✓ {client_name}: OK ({len(rates)} rates)")
                successful_sources.append(client_name)

            except ApiRequestError as e:
                error_msg = f"✗ {client_name}: FAILED - {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

            except Exception as e:
                error_msg = f"✗ {client_name}: UNEXPECTED ERROR - {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Если хотя бы один источник успешен - сохраняем данные
        if all_rates:
            try:
                logger.info(f"Writing {len(all_rates)} rates to storage...")
                self.storage.save_current_rates(all_rates, source_map)
                self.storage.append_to_history(all_rates, source_map)
                logger.info("✓ Successfully saved to storage")
            except Exception as e:
                error_msg = f"Failed to save to storage: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Формируем результат
        result = {
            "success": len(all_rates) > 0,
            "total_rates": len(all_rates),
            "successful_sources": successful_sources,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        logger.info("=" * 60)
        if errors:
            logger.warning(f"Update completed with {len(errors)} error(s)")
        else:
            logger.info("Update completed successfully")
        logger.info("=" * 60)

        return result


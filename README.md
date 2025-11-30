# finalproject_Masenkova_M25-555
Консольное приложение для симуляции торговли валютами (фиатные и криптовалюты).

## Установка

make install

## Запуск

make project

или

poetry run project


## Разработка

Проверить код (PEP8):
make lint

Сборка пакета:
make build

## Структура проекта

- `valutatrade_hub/` — основной пакет
  - `core/` — бизнес-логика (модели, исключения)
  - `infra/` — инфраструктура (settings, database)
  - `parser_service/` — сервис парсинга курсов
  - `cli/` — командный интерфейс
- `data/` — JSON-файлы с данными
- `logs/` — логи приложения

## Команды CLI

- `register --username <name> --password <pass>` — регистрация
- `login --username <name> --password <pass>` — вход
- `show-portfolio [--base USD]` — показать портфель
- `buy --currency BTC --amount 0.05` — купить валюту
- `sell --currency BTC --amount 0.05` — продать валюту
- `get-rate --from USD --to BTC` — получить курс
- `update-rates` — обновить курсы из API
- `show-rates [--currency BTC]` — показать кэш курсов

## Зависимости

- Python 3.9+
- Poetry (управление зависимостями)
- prettytable (форматирование таблиц)
- requests (HTTP-запросы к API)
- ruff (линтер, разработка)


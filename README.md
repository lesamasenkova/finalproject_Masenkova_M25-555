# ValutaTrade Hub

Консольное приложение для управления валютным кошельком с поддержкой фиатных и криптовалют.

## Описание

ValutaTrade Hub — это инструмент для управления виртуальным портфелем валют с автоматическим обновлением курсов через внешние API (CoinGecko, ExchangeRate-API).

### Основные возможности

- Регистрация и аутентификация пользователей
- Покупка и продажа 12+ валют (фиат + крипто)
- Автоматическое обновление курсов валют
- Просмотр портфеля в разных базовых валютах
- История операций в логах
- Чистая архитектура (Clean Architecture)

## Технологии

- Python 3.9+
- Poetry (управление зависимостями)
- Requests (HTTP клиент)
- PrettyTable (табличный вывод)
- Ruff (линтер)

## Установка

### 1. Клонируйте репозиторий

```bash
git clone <repository_url>
cd valutatrade_hub
```

### 2. Установите зависимости

```bash
make install
```

Или вручную:

```bash
poetry install
```

### 3. Настройте окружение

```bash
make setup
```

Эта команда создаст:
- Директории `data/` и `logs/`
- Файл `.env` из шаблона `.env.example`

### 4. Получите API ключ

1. Перейдите на https://www.exchangerate-api.com/
2. Зарегистрируйтесь и получите бесплатный API ключ
3. Откройте `.env` и добавьте ключ:

```bash
EXCHANGERATE_API_KEY=ваш_ключ_здесь
```

## Запуск

### Через Make

```bash
make project
```

### Через Poetry

```bash
poetry run project
```

### Напрямую

```bash
python3 main.py
```

## Использование

### Регистрация и вход

```bash
# Зарегистрировать пользователя
> register --username alice --password secret123

# Войти в систему
> login --username alice --password secret123
```

### Управление валютами

```bash
# Показать список поддерживаемых валют
> list-currencies

# Обновить курсы валют
> update-rates

# Показать текущие курсы из кеша
> show-rates

# Получить курс конкретной пары
> get-rate --from BTC --to USD
```

### Операции с портфелем

```bash
# Купить валюту
> buy --currency BTC --amount 0.5

# Продать валюту
> sell --currency BTC --amount 0.2

# Показать портфель (в USD по умолчанию)
> show-portfolio

# Показать портфель в другой валюте
> show-portfolio --base EUR
```

### Другие команды

```bash
# Выйти из аккаунта
> logout

# Показать справку
> help

# Выйти из приложения
> exit
```

## Структура проекта

```
valutatrade_hub/
├── valutatrade_hub/          # Основной пакет
│   ├── core/                 # Доменный слой
│   │   ├── currencies.py     # Иерархия валют
│   │   ├── models.py         # User, Portfolio, Wallet
│   │   ├── usecases.py       # Бизнес-логика
│   │   ├── utils.py          # Вспомогательные функции
│   │   └── exceptions.py     # Кастомные исключения
│   ├── infra/                # Инфраструктурный слой
│   │   ├── database.py       # Работа с JSON
│   │   └── settings.py       # Конфигурация
│   ├── parser_service/       # Сервис парсинга курсов
│   │   ├── api_clients.py    # API клиенты
│   │   ├── config.py         # Конфигурация парсера
│   │   ├── storage.py        # Хранилище курсов
│   │   └── updater.py        # Координатор обновлений
│   └── cli/                  # Слой представления
│       └── interface.py      # CLI интерфейс
├── decorators.py             # Декоратор логирования
├── main.py                   # Точка входа
├── data/                     # Данные (создается автоматически)
│   ├── currencies.json       # Реестр валют
│   ├── users.json            # Пользователи
│   ├── portfolios.json       # Портфели
│   ├── rates.json            # Текущие курсы
│   └── exchange_rates.json   # История курсов
├── logs/                     # Логи (создается автоматически)
│   └── actions.log           # Лог операций
├── pyproject.toml            # Конфигурация Poetry
├── Makefile                  # Команды для сборки
├── .env.example              # Шаблон переменных окружения
└── README.md                 # Этот файл
```

## Тестирование

```bash
# Запустить линтер
make lint

# Автоматическое исправление стиля
make format

# Запустить тесты (если добавлены)
make test
```

## Разработка

### Добавление новой валюты

Отредактируйте `data/currencies.json`:

```json
{
  "fiat": [
    {"code": "CHF", "name": "Swiss Franc", "issuing_country": "Switzerland"}
  ],
  "crypto": [
    {"code": "ADA", "name": "Cardano", "algorithm": "Ouroboros", "market_cap": 1.5e10}
  ]
}
```

Перезапустите приложение для применения изменений.

### Поддерживаемые валюты по умолчанию

**Фиатные:**
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- RUB (Russian Ruble)
- JPY (Japanese Yen)
- CNY (Chinese Yuan)

**Криптовалюты:**
- BTC (Bitcoin)
- ETH (Ethereum)
- SOL (Solana)
- USDT (Tether)
- BNB (Binance Coin)
- XRP (Ripple)

## Логирование

Все операции логируются в `logs/actions.log`:

```
2026-01-12 23:00:00 - REGISTER user='alice' result=OK
2026-01-12 23:01:15 - LOGIN user='alice' result=OK
2026-01-12 23:02:30 - BUY user='alice' currency='BTC' amount=0.5 result=OK
```

## Автор

Студент группы M25-555

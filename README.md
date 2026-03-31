# Telegram Bot Service

Production-ready Telegram бот с поддержкой webhook/polling, PostgreSQL 17 и DI.

## Быстрый старт

```bash
# Клонирование
git clone &lt;repo&gt;
cd telegram-bot

# Настройка окружения
cp .env.example .env
# Отредактируй .env файл

# Запуск миграций
poetry run alembic upgrade head

# Запуск в polling режиме
poetry run python -m src.main

# Запуск в webhook режиме
BOT_MODE=webhook poetry run python -m src.main

# Сборка и запуск
docker-compose up -d --build

# Масштабирование (3 инстанса)
docker-compose up -d --scale bot-1=1 --scale bot-2=1 --scale bot-3=1

# Просмотр логов
open http://localhost:9999  # Dozzle
```

## Сборка и запуск

docker-compose up -d --build

## Масштабирование (3 инстанса)

docker-compose up -d --scale bot-1=1 --scale bot-2=1 --scale bot-3=1

## Просмотр логов

open <http://localhost:9999>  # Dozzle

Деплой
GitHub Actions автоматически деплоит при push в main. Требуется настройка
secrets: SSH_HOST, SSH_USER, SSH_PRIVATE_KEY.
SSH туннель используется для безопасной отправки образов в приватный registry
без открытия порта 5000 наружу.

## Генерация новой миграции

alembic revision -m "add new feature" --autogenerate

## Ручное создание SQL миграции

alembic revision -m "optimize indexes"

## Применение миграций

alembic upgrade head

## Откат на 1 версию назад

alembic downgrade -1

## Проверка текущей версии

alembic current

## История

alembic history --verbose

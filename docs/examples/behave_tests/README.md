реализация BDD-тестов с Behave для диалогов бота. Тесты запускают реальный бот в testcontainers и проверяют сценарии через имитацию Telegram API.
Структура проекта

dialog_bot/
├── features/
│   ├── steps/
│   │   ├── bot_steps.py       # Шаги для взаимодействия с ботом
│   │   ├── db_steps.py        # Шаги для проверки БД
│   │   └── context.py         # Фикстуры и хелперы
│   ├── order_dialog.feature   # Сценарии заказа
│   └── support_ticket.feature # Сценарии поддержки
├── tests/
│   └── behave_environment.py  # Настройка окружения
└── behave.ini                 # Конфигурация

Запуск тестов

# Установка зависимостей

pip install behave pytest-asyncio testcontainers

# Запуск всех сценариев

behave

# Запуск конкретного feature

behave features/order_dialog.feature

# Запуск с тегами

behave --tags=~wip  # исключая WIP

# Показать отладку

behave --logging-level=DEBUG -v

# Генерация отчета

behave --format=allure_behave.formatter:AllureFormatter -o allure-results/

Ключевые особенности
====================

Компонент Назначение
-----------------------

TestUser Модель пользователя для тестов
DialogContext Отслеживание истории диалога
BotTestClient HTTP-клиент для имитации Telegram
@async_run_until_complete Декоратор для async шагов
PostgresContainer Изолированная БД для каждого теста

Тесты проверяют не только ответы бота, но и состояние в PostgreSQL, что критично для FSM с восстановлением состояния.

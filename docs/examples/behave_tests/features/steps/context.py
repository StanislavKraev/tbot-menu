from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp
from testcontainers.postgres import PostgresContainer


@dataclass
class TestUser:
    """Модель тестового пользователя."""

    id: int = 123456789
    username: str = "test_user"
    first_name: str = "Test"
    last_name: str = "User"
    language_code: str = "ru"


@dataclass
class DialogContext:
    """Контекст диалога для BDD."""

    user: TestUser = field(default_factory=TestUser)
    chat_id: int = 123456789
    thread_id: int | None = None
    current_state: str | None = None
    last_response: str | None = None
    conversation_history: list[dict[str, Any]] = field(default_factory=list)

    def add_message(self, direction: str, text: str, **kwargs):
        """Добавляет сообщение в историю."""
        self.conversation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "direction": direction,  # "in" (к боту) или "out" (от бота)
                "text": text,
                **kwargs,
            }
        )


class BotTestClient:
    """Клиент для тестирования бота через HTTP webhook."""

    def __init__(self, base_url: str, bot_token: str):
        self.base_url = base_url
        self.bot_token = bot_token
        self.session: aiohttp.ClientSession | None = None

    async def connect(self):
        self.session = aiohttp.ClientSession()

    async def disconnect(self):
        if self.session:
            await self.session.close()

    async def send_message(self, user: TestUser, text: str, chat_id: int, thread_id: int | None = None) -> str | None:
        """Отправляет сообщение боту через webhook."""
        # Формируем Update объект как пришло бы от Telegram
        update = {
            "update_id": int(datetime.now().timestamp()),
            "message": {
                "message_id": int(datetime.now().timestamp() * 1000) % 100000,
                "from": {
                    "id": user.id,
                    "is_bot": False,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "language_code": user.language_code,
                },
                "chat": {
                    "id": chat_id,
                    "type": "private" if thread_id is None else "supergroup",
                    "title": "Test Group" if thread_id else None,
                },
                "date": int(datetime.now().timestamp()),
                "text": text,
            },
        }

        # Добавляем thread_id если есть
        if thread_id:
            update["message"]["message_thread_id"] = thread_id
            update["message"]["is_topic_message"] = True

        # Отправляем на webhook
        webhook_url = f"{self.base_url}/webhook"

        async with self.session.post(webhook_url, json=update) as resp:
            if resp.status == 200:
                # В реальном тесте здесь нужно перехватить ответ бота
                # Через мок Bot.send_message или очередь сообщений
                return await self._get_last_bot_response(user.id, chat_id, thread_id)
            return None

    async def _get_last_bot_response(self, user_id: int, chat_id: int, thread_id: int | None = None) -> str | None:
        """Получает последний ответ бота (через мок или БД)."""
        # В тестовом режиме бот пишет в in-memory очередь
        # или мы проверяем состояние через API
        from features.steps.mock_bot import get_last_message

        return get_last_message(user_id, chat_id, thread_id)


# Глобальный контейнер PostgreSQL для всех тестов
_postgres_container: PostgresContainer | None = None


async def start_test_environment(context):
    """Запускает тестовое окружение."""
    global _postgres_container

    # 1. Запускаем PostgreSQL
    _postgres_container = PostgresContainer("postgres:17-alpine")
    _postgres_container.start()

    db_url = _postgres_container.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")

    # 2. Применяем миграции
    import subprocess

    env = os.environ.copy()
    env["DB_URL"] = db_url
    subprocess.run(["alembic", "upgrade", "head"], env=env, check=True)

    # 3. Запускаем бот в тестовом режиме (без реального webhook)
    from src.main import create_test_app

    context.app = create_test_app(db_url=db_url)

    # 4. Инициализируем клиент
    context.bot_client = BotTestClient(base_url="http://localhost:8080", bot_token="test_token")
    await context.bot_client.connect()

    # 5. Контекст диалога
    context.dialog = DialogContext()

    # 6. Подключение к БД для проверок
    from sqlalchemy.ext.asyncio import create_async_engine

    context.db_engine = create_async_engine(db_url)


async def stop_test_environment(context):
    """Останавливает тестовое окружение."""
    await context.bot_client.disconnect()
    await context.db_engine.dispose()

    if _postgres_container:
        _postgres_container.stop()


def get_db_connection(context):
    """Возвращает соединение с тестовой БД."""
    return context.db_engine

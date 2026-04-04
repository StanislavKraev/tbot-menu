import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine

from src.adapters.state_storage import StateStorage
from src.containers import AppContainer
from src.handlers.general_lead_magnit import create_general_lm_router


@dataclass
class UserContext:
    """Контекст тестового пользователя"""

    user_id: int
    chat_id: int
    username: str = "test_user"
    messages_sent: list[dict[str, Any]] = field(default_factory=list)
    last_message_id: int = 0
    bot: Bot | None = None

    def get_next_message_id(self) -> int:
        self.last_message_id += 1
        return self.last_message_id

    def get_last_message(self) -> dict[str, Any]:
        assert self.messages_sent, "No messages sent"
        return self.messages_sent[-1]


@pytest_asyncio.fixture
async def user_context() -> UserContext:
    """Фикстура контекста пользователя"""
    return UserContext(user_id=123456, chat_id=123456)


@pytest_asyncio.fixture
async def bot(user_context: UserContext) -> AsyncMock:
    """Мок бота с перехватом сообщений"""
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.token = "test-token"

    async def universal_capture(*args, **kwargs):
        if args:
            message: SendMessage = args[0]
        else:
            return AsyncMock()
        msg = {
            "chat_id": message.chat_id,
            "text": message.text,
            "message_thread_id": kwargs.get("message_thread_id"),
            "reply_markup": kwargs.get("reply_markup"),
            "parse_mode": kwargs.get("parse_mode"),
        }
        user_context.messages_sent.append(msg)
        # Возвращаем фейковый Message
        return Message(
            message_id=len(user_context.messages_sent),
            date=datetime.now(),
            chat=Chat(id=message.chat_id, type="private"),
            text=message.text,
            bot=mock_bot,
        )

    mock_bot.side_effect = universal_capture
    # mock_bot.send_photo = AsyncMock()
    # mock_bot.send_document = AsyncMock()
    user_context.bot = mock_bot

    return mock_bot


@pytest_asyncio.fixture
async def db_engine(postgres_dsn: str):
    """Async engine для тестов из существующего sync engine"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    # Конвертируем DSN в asyncpg
    dsn = postgres_dsn.replace("postgresql+psycopg2", "postgresql+asyncpg")
    engine = create_async_engine(dsn, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_container(container: AppContainer, db_engine) -> AppContainer:
    """Контейнер с async движком БД"""
    # Переопределяем engine на async
    container.db_engine.override(db_engine)
    return container


@pytest_asyncio.fixture
async def state_storage(container: AppContainer, db_engine: AsyncEngine) -> StateStorage:
    """FSM-хранилище на тестовой БД"""
    # Используем движок из контейнера или переданный
    storage = StateStorage(engine=db_engine)
    return storage


@pytest_asyncio.fixture
async def dispatcher(bot: AsyncMock, state_storage: StateStorage, container: AppContainer) -> Dispatcher:
    """Диспатчер с подключенным роутером"""
    dp = Dispatcher(storage=state_storage)
    dp.include_router(create_general_lm_router())

    # Передаем бота в контекст (как в реальном приложении)
    dp["bot"] = bot
    dp["container"] = container

    return dp


@pytest_asyncio.fixture
async def fsm_context(dispatcher: Dispatcher, user_context: UserContext) -> FSMContext:
    """FSM контекст для прямого манипулирования состоянием"""
    storage_key = StorageKey(
        bot_id=1,  # фейковый ID бота
        chat_id=user_context.chat_id,
        user_id=user_context.user_id,
    )
    return FSMContext(storage=dispatcher.storage, key=storage_key)


def create_message(user_context: UserContext, text: str, chat_id: int = None) -> Message:
    """Фабрика сообщений"""
    chat_id = chat_id or user_context.chat_id

    user = User(id=user_context.user_id, is_bot=False, first_name="Test", username=user_context.username)

    chat = Chat(id=chat_id, type="private")

    return Message(
        message_id=user_context.get_next_message_id(),
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text,
        bot=user_context.bot,
    )


async def process_update(dispatcher: Dispatcher, bot: AsyncMock, message: Message) -> None:
    """Обработка сообщения через диспатчер"""
    update = Update(update_id=1, message=message)
    await dispatcher.feed_update(bot=bot, update=update)
    await asyncio.sleep(0)


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    """Логируем начало шага"""
    logger.info(f"▶️  STEP START: {step.keyword} {step.name}")
    # Можно также сохранить в request.node для доступа в отчете
    request.node.current_step = f"{step.keyword} {step.name}"


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    """Логируем успешное завершение"""
    logger.info(f"✅ STEP PASS:  {step.keyword} {step.name}")


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Логируем ошибку с деталями"""
    logger.error(f"❌ STEP FAIL:  {step.keyword} {step.name}")
    logger.error(f"   Exception: {exception}")
    # Добавляем имя шага к сообщению об ошибке для отображения в отчете
    exception.step_name = f"{step.keyword} {step.name}"

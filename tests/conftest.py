from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import Engine, NullPool, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from src.config import Settings
from src.containers import AppContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    """Запуск PostgreSQL в контейнере."""
    with PostgresContainer("postgres:17-alpine") as postgres:
        yield postgres


@pytest.fixture
def postgres_dsn(postgres_container: PostgresContainer) -> str:
    """Создание engine для тестов."""
    connection_url = postgres_container.get_connection_url().replace("postgresql+asyncpg", "postgresql+psycopg2")
    return connection_url  # type: ignore


@pytest.fixture
def db(postgres_dsn: str) -> Generator[Engine]:
    """Инициализация БД с SQL миграциями вместо create_all."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    engine = create_engine(postgres_dsn)

    # Применяем миграции через Alembic
    alembic_cfg = Config(Path(__file__).parent.parent / "alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url", str(postgres_dsn).replace("postgresql+asyncpg", "postgresql+psycopg2")
    )
    alembic_cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "migrations"))

    command.upgrade(alembic_cfg, "head")

    yield engine

    # Очистка: TRUNCATE всех таблиц
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE pdf_files, users RESTART IDENTITY CASCADE"))

    engine.dispose()


@pytest.fixture
def settings(postgres_dsn: str) -> Settings:
    return Settings(
        bot_token="test-token",
        admin_telegram_id=111,
        database_conn=postgres_dsn,
    )


@pytest.fixture
def container(settings: Settings, postgres_dsn: str, db: Engine) -> Generator[AppContainer]:
    def _domain_container() -> AppContainer:
        return container  # type: ignore[return-value]

    postgres_async_engine = create_async_engine(
        postgres_dsn.replace("+psycopg2", "").replace("postgresql:", "postgresql+asyncpg:"),
        poolclass=NullPool,
    )

    from src import main as app_module

    with patch.object(app_module, "AppContainer", _domain_container):
        container = AppContainer()
        container.config.from_pydantic(settings)
        container.db_engine.override(postgres_async_engine)
        yield container

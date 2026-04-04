from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import settings


class Database:
    _engine: AsyncEngine | None = None

    @classmethod
    async def connect(cls):
        cls._engine = create_async_engine(settings.db_url, pool_size=10, max_overflow=20)

    @classmethod
    async def disconnect(cls):
        if cls._engine:
            await cls._engine.dispose()

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        if not cls._engine:
            raise RuntimeError("DB not connected")
        return cls._engine


async def get_db():
    """Dependency для FastAPI."""
    return Database.get_engine()

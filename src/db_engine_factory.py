"""Database engine caching factory."""

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def db_engine_factory() -> Callable[[str, int, int, bool], AsyncEngine]:
    def _factory(
        url: str,
        pool_size: int,
        max_overflow: int,
        pool_pre_ping: bool,
    ) -> AsyncEngine:
        engine = create_async_engine(
            url=url.replace("postgresql://", "postgresql+asyncpg://"),
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
        )
        return engine

    return _factory

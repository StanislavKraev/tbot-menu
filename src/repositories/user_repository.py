from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncEngine

from src.models.tables import users


class UserRepository:
    """Репозиторий пользователей на SQLAlchemy Core."""

    def __init__(self, db: AsyncEngine) -> None:
        self._db = db

    async def get_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        """Получение пользователя по telegram_id с использованием covering index."""
        async with self._db.begin() as conn:
            stmt = select(users.c.id, users.c.telegram_id, users.c.username, users.c.created_at).where(
                users.c.telegram_id == telegram_id
            )

            result = await conn.execute(stmt)
            row = result.fetchone()
            return row._asdict() if row else None

    async def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
        utm_source: str | None,
    ) -> dict[str, Any]:
        """Создание пользователя с возвратом созданной записи."""
        async with self._db.begin() as conn:
            stmt = (
                insert(users)
                .values(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code,
                    utm_source=utm_source,
                )
                .returning(users.c.id, users.c.telegram_id, users.c.created_at)
            )
            result = await conn.execute(stmt)
            row = result.fetchone()
            if not row:
                raise RuntimeError()
            return row._asdict()

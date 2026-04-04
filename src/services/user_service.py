# src/services/user_service.py
from typing import Any

from src.adapters.user_repository import UserRepository


class UserService:
    """Сервис управления пользователями."""

    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def register_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
        utm_source: str | None = None,
    ) -> dict[str, Any]:
        """Регистрация нового пользователя или возврат существующего."""
        existing = await self._repo.get_by_telegram_id(telegram_id)
        if existing:
            return existing

        return await self._repo.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            utm_source=utm_source,
        )

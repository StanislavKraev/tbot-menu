import json
from collections.abc import Mapping
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


def get_state_id(state: StateType = None) -> str | None:
    if not state:
        return None
    if isinstance(state, State):
        return state.state
    return state


class StateStorage(BaseStorage):
    """Кастомное хранилище FSM состояний в PostgreSQL."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        state_str = get_state_id(state)

        async with self._engine.connect() as conn:
            await conn.execute(
                text("""
                    INSERT INTO dialog_states (user_id, chat_id, state, data, updated_at)
                    VALUES (:user_id, :chat_id, :state, '{}', NOW())
                    ON CONFLICT (user_id, chat_id)
                    DO UPDATE SET
                        state = EXCLUDED.state,
                        updated_at = NOW()
                """),
                {"user_id": key.user_id, "chat_id": key.chat_id, "state": state_str or ""},
            )
            await conn.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        async with self._engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT state FROM dialog_states
                    WHERE user_id = :user_id AND chat_id = :chat_id
                """),
                {"user_id": key.user_id, "chat_id": key.chat_id},
            )
            row = result.fetchone()
            return row.state if row and row.state else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        async with self._engine.connect() as conn:
            await conn.execute(
                text("""
                    INSERT INTO dialog_states (user_id, chat_id, state, data, updated_at)
                    VALUES (:user_id, :chat_id, '', :data, NOW())
                    ON CONFLICT (user_id, chat_id)
                    DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = NOW()
                """),
                {"user_id": key.user_id, "chat_id": key.chat_id, "data": json.dumps(data)},
            )
            await conn.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with self._engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT data FROM dialog_states
                    WHERE user_id = :user_id AND chat_id = :chat_id
                """),
                {"user_id": key.user_id, "chat_id": key.chat_id},
            )
            row = result.fetchone()
            return row.data if row and row.data else {}

    async def update_data(self, key: StorageKey, data: Mapping[str, Any]) -> dict[str, Any]:
        current = await self.get_data(key)
        current.update(data)
        await self.set_data(key, current)
        return dict(data)

    async def clear(self, key: StorageKey) -> None:
        async with self._engine.connect() as conn:
            await conn.execute(
                text("""
                    DELETE FROM dialog_states
                    WHERE user_id = :user_id AND chat_id = :chat_id
                """),
                {"user_id": key.user_id, "chat_id": key.chat_id},
            )
            await conn.commit()

    async def close(self) -> None:
        """Close storage (database connection, file or etc.)."""
        pass

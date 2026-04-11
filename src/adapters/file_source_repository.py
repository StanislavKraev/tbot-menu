from typing import Any

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncEngine

from src.models.schemas import (
    FileSource, S3Source, YandexDiskSource,
    FileSourceType, LocalStorageSource, TelegramFileSource
)
from src.models.tables import file_sources


class FileSourceRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def add_source(
            self,
            pdf_file_id: int,
            source: FileSource,
    ) -> int:
        """
        Добавляет источник к PDF. Если is_primary=True, сбрасывает флаг у других.
        """
        async with self._engine.begin() as conn:

            # Pydantic v2: model_dump() сериализует в dict
            source_data = source.model_dump(exclude={"source_type"}, by_alias=True)

            stmt = insert(file_sources).values(
                pdf_file_id=pdf_file_id,
                source_type=source.source_type.value,
                data=source_data  # SQLAlchemy автоматически конвертирует dict в JSONB
            ).returning(file_sources.c.id)

            result = await conn.execute(stmt)
            return result.scalar_one()

    async def get_all_sources(
            self,
            pdf_file_id: int,
            source_type: FileSourceType | None = None
    ) -> list[FileSource]:
        """Получает все источники файла с опциональной фильтрацией по типу."""
        async with self._engine.begin() as conn:
            stmt = select(file_sources).where(
                file_sources.c.pdf_file_id == pdf_file_id
            )

            if source_type:
                stmt = stmt.where(file_sources.c.source_type == source_type.value)

            stmt = stmt.order_by(file_sources.c.sort_order, file_sources.c.created_at)
            result = await conn.execute(stmt)
            rows = result.fetchall()

            return [self._deserialize_row(row) for row in rows if row]

    async def update_source_data(
            self,
            source_id: int,
            new_data: FileSource
    ) -> None:
        """Обновляет данные источника (например, обновить direct_url у Яндекса)."""
        async with self._engine.begin() as conn:
            stmt = (
                update(file_sources)
                .where(file_sources.c.id == source_id)
                .values(
                    source_type=new_data.source_type.value,
                    data=new_data.model_dump(exclude={"source_type"}),
                    display_name=self._generate_display_name(new_data)
                )
            )
            await conn.execute(stmt)

    async def get_sources_by_type(
            self,
            source_type: FileSourceType,
            limit: int = 100
    ) -> list[tuple[int, FileSource]]:  # (pdf_file_id, source)
        """Поиск по типу (использует денормализованное поле source_type)."""
        async with self._engine.begin() as conn:
            stmt = (
                select(file_sources.c.pdf_file_id, file_sources.c.data)
                .where(file_sources.c.source_type == source_type.value)
                .limit(limit)
            )
            result = await conn.execute(stmt)

            return [
                (row.pdf_file_id, self._deserialize_raw(row.data, source_type))
                for row in result.fetchall()
            ]

    def _deserialize_row(self, row: Any) -> FileSource:
        """Десериализация из строки БД."""
        data = dict(row.data)  # JSONB -> dict
        data["source_type"] = row.source_type  # Добавляем дискриминатор

        # Используем Pydantic для валидации и создания конкретного класса
        return self._deserialize_raw(data, FileSourceType(row.source_type))

    def _deserialize_raw(self, data: dict, source_type: FileSourceType) -> FileSource:
        """Создание конкретного экземпляра по типу."""
        mapping = {
            FileSourceType.S3: S3Source,
            FileSourceType.YANDEX_DISK: YandexDiskSource,
            FileSourceType.LOCAL: LocalStorageSource,
            FileSourceType.TELEGRAM: TelegramFileSource,
        }

        model_class = mapping.get(source_type)
        if not model_class:
            raise ValueError(f"Unknown source type: {source_type}")

        return model_class(**data)

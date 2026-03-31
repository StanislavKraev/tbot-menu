from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from src.models.tables import pdf_files


class PdfRepository:
    """Репозиторий для управления PDF файлами."""

    def __init__(self, db: AsyncEngine) -> None:
        self._db = db

    async def get_active_pdf(self) -> dict[str, Any] | None:
        """Получение активного PDF файла."""
        async with self._db.begin() as conn:
            stmt = (
                select(pdf_files.c.id, pdf_files.c.filename, pdf_files.c.yandex_url)
                .where(pdf_files.c.is_active == "1")
                .order_by(pdf_files.c.updated_at.desc())
                .limit(1)
            )

            result = await conn.execute(stmt)
            row = result.fetchone()
            return row._asdict() if row else None

    async def save_pdf_url(self, filename: str, url: str) -> dict[str, Any]:
        """Сохранение новой ссылки на PDF (деактивирует старые)."""
        async with self._db.begin() as conn:
            # Деактивируем старые
            await conn.execute(update(pdf_files).where(pdf_files.c.is_active == "1").values(is_active="0"))

            # Вставляем новый
            stmt = (
                insert(pdf_files)
                .values(filename=filename, yandex_url=url, is_active="1")
                .returning(pdf_files.c.id, pdf_files.c.yandex_url)
            )
            result = await conn.execute(stmt)
            row = result.fetchone()
            if not row:
                raise RuntimeError()
            return row._asdict()

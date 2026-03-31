from typing import Any

import httpx
from loguru import logger

from src.repositories.pdf_repository import PdfRepository


class PdfService:
    """Сервис для работы с PDF файлами на Yandex Disk."""

    def __init__(self, repository: PdfRepository) -> None:
        self._repo = repository
        limits = httpx.Limits(
            max_connections=30,
            max_keepalive_connections=20,
        )
        self._client = httpx.AsyncClient(http2=True, limits=limits, timeout=10.0)

    async def get_current_pdf_url(self) -> str | None:
        """Получение URL текущего активного PDF."""
        pdf = await self._repo.get_active_pdf()
        return pdf["yandex_url"] if pdf else None

    async def update_pdf_link(self, filename: str, url: str) -> dict[str, Any]:
        """Обновление ссылки на PDF (для админки)."""
        return await self._repo.save_pdf_url(filename, url)

    async def download_pdf(self, url: str) -> bytes | None:
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            return await resp.aread()
        except Exception as e:  # NoQA: BLE001
            logger.error(f"Error downloading PDF: {e}")
            return None

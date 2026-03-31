import pytest

from src.containers import AppContainer


@pytest.mark.asyncio
async def test_pdf_update(container: AppContainer) -> None:
    """Тест обновления PDF админом."""
    service = container.pdf_service()

    # Обновляем PDF
    result = await service.update_pdf_link("doc.pdf", "https://disk.yandex.ru/test1")
    assert result["yandex_url"] == "https://disk.yandex.ru/test1"

    # Проверяем что он стал активным
    current = await service.get_current_pdf_url()
    assert current == "https://disk.yandex.ru/test1"

    # Добавляем новый - старый должен деактивироваться
    await service.update_pdf_link("doc2.pdf", "https://disk.yandex.ru/test2")
    current = await service.get_current_pdf_url()
    assert current == "https://disk.yandex.ru/test2"

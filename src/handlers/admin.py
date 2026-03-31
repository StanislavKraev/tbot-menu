from aiogram import Router, types
from aiogram.filters import Command
from loguru import logger

from src.config import Settings
from src.services.pdf_service import PdfService

router = Router()


@router.message(Command("setpdf"))
async def cmd_set_pdf(message: types.Message, config: Settings, pdf_service: PdfService) -> None:
    """Команда для обновления ссылки на PDF (только для админа)."""
    # Проверка прав администратора
    if not config.admin_telegram_id:
        return

    from_user = message.from_user
    if from_user is None:
        logger.error("from User is None")
        return

    if from_user.id != config.admin_telegram_id:
        logger.warning(f"Unauthorized admin access attempt: {from_user.id}")
        return

    # Парсинг аргументов: /setpdf <url> [filename]
    message_text: str = message.text or ""
    parts = message_text.split(" ", 2)
    if len(parts) < 2:
        await message.answer("⚠️ Использование: /setpdf <yandex_url> [filename]")
        return

    url = parts[1]
    filename = parts[2] if len(parts) > 2 else "document.pdf"

    try:
        result = await pdf_service.update_pdf_link(filename, url)
        await message.answer(f"✅ PDF обновлен!\nID: {result['id']}\nURL: {result['yandex_url']}")
        logger.info(f"PDF updated by admin {from_user.id}: {url}")
    except Exception as e:  # NoQA: BLE001
        logger.error(f"Failed to update PDF: {e}")
        await message.answer(f"❌ Ошибка обновления: {e}")

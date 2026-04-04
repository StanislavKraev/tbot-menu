from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger


def create_admin_router() -> Router:
    router = Router()

    @router.message(F.document, Command("uploadpdf"))
    async def upload_pdf_handler(message: Message, admin_telegram_id: int) -> None:
        """Команда для загрузки PDF и получения file_id.

        Только для администратора.
        """
        if not message.from_user or message.from_user.id != admin_telegram_id:
            await message.answer("⛔ Только для администратора")
            return

        document = message.document

        # Проверяем что это PDF
        if not document or not document.file_name or not document.file_name.endswith(".pdf"):
            await message.answer("❌ Нужно отправить файл в формате PDF")
            return

        file_id = document.file_id
        file_name = document.file_name
        file_size = document.file_size

        # Логируем в консоль/файл
        logger.info(f"📄 PDF загружен: {file_name}")
        logger.info(f"📎 File ID: {file_id}")
        logger.info(f"📊 Размер: {file_size} bytes")

        # Отправляем file_id обратно админу для копирования
        await message.answer(
            f"✅ <b>PDF получен!</b>\n\n"
            f"📁 Файл: <code>{file_name}</code>\n"
            f"🆔 <b>File ID:</b>\n"
            f"<code>{file_id}</code>\n\n"
            f"💾 Сохраните этот ID в .env или БД для рассылки",
            parse_mode="HTML",
        )

    return router

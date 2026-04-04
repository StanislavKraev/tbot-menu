from aiogram import Router, flags, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from loguru import logger

from src.services.pdf_service import PdfService
from src.services.user_service import UserService


def parse_utm(payload: str) -> str | None:
    """Парсинг UTM из payload команды /start."""
    if not payload:
        return None

    # Поддержка форматов: /start utm_source=telegram или /start telegram
    if "=" in payload:
        parts = payload.split("=")
        if len(parts) == 2 and parts[0].strip().lower() in ("utm_source", "source"):
            return parts[1].strip()
    return payload.strip()


def create_strart_router() -> Router:
    start_router = Router()

    @start_router.message(Command("start"))
    @flags.chat_action(initial_sleep=0, action="upload_document", interval=2)
    async def cmd_start(message: types.Message, user_service: UserService, pdf_service: PdfService) -> None:
        """Обработчик команды /start."""
        # Извлекаем UTM
        message_text: str = message.text or ""
        payload = message_text.split(" ", 1)[1] if " " in message_text else ""
        utm_source = parse_utm(payload)

        from_user = message.from_user
        if not from_user:
            return

        logger.info(f"User {from_user.id} started with UTM: {utm_source}")

        # Сохраняем пользователя
        try:
            await user_service.register_user(
                telegram_id=from_user.id,
                username=from_user.username,
                first_name=from_user.first_name,
                last_name=from_user.last_name,
                language_code=from_user.language_code,
                utm_source=utm_source,
            )
        except Exception:  # NoQA
            logger.exception("Failed to register user")
            return

        # Приветственное сообщение
        await message.answer("👋 Добро пожаловать! Подготавливаем ваш файл...")

        # Получаем PDF
        pdf_url = await pdf_service.get_current_pdf_url()
        if not pdf_url:
            await message.answer("❌ Файл временно недоступен. Попробуйте позже.")
            return

        # Скачиваем и отправляем PDF
        pdf_data = await pdf_service.download_pdf(pdf_url)
        if not pdf_data:
            await message.answer("❌ Не удалось загрузить файл. Попробуйте позже.")
            return

        # Отправляем как документ
        file = BufferedInputFile(pdf_data, filename="document.pdf")
        await message.answer_document(document=file, caption="✅ Ваш файл готов!")

    return start_router

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from src.adapters.state_storage import StateStorage
from src.handlers.admin import create_admin_router
from src.handlers.general_lead_magnit import create_general_lm_router
from src.handlers.start import create_strart_router
from src.services.pdf_service import PdfService
from src.services.user_service import UserService


class BotInitializer:
    """Инициализация бота и диспетчера."""

    def __init__(
        self,
        bot_token: str,
        user_service: UserService,
        pdf_service: PdfService,
        state_storage: StateStorage,
    ) -> None:
        self.user_service = user_service
        self.pdf_service = pdf_service
        self.bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher(storage=state_storage)
        self._setup_routers()

    def _setup_routers(self) -> None:
        """Настройка роутеров с внедрением зависимостей."""
        # Передаем сервисы в хендлеры через middleware или контекст
        main_router = Router()

        # В Aiogram 3.x можно использовать middleware для передачи зависимостей
        main_router.include_router(create_strart_router())
        main_router.include_router(create_admin_router())

        # Устанавливаем контекстные данные
        self.dp["user_service"] = self.user_service
        self.dp["pdf_service"] = self.pdf_service

        self.dp.include_router(main_router)
        self.dp.include_router(create_general_lm_router())

    async def setup_commands(self) -> None:
        """Установка команд меню."""
        commands = [
            BotCommand(command="start", description="Начать работу"),
            BotCommand(command="order", description="Сделать заказ"),
        ]
        await self.bot.set_my_commands(commands)

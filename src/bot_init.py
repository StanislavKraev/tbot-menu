from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from src.adapters.state_storage import StateStorage
from src.handlers.admin import create_admin_router
from src.handlers.general_lead_magnit import create_general_lm_router
from src.services.pdf_service import PdfService
from src.services.user_service import UserService


class DependencyMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]
    ) -> Any:
        # Извлекаем сервисы из контекста диспатчера
        dispatcher = data["dispatcher"]
        data["user_service"] = dispatcher["user_service"]
        data["pdf_service"] = dispatcher["pdf_service"]
        data["admin_id"] = dispatcher.get("admin_telegram_id")


class BotInitializer:
    """Инициализация бота и диспетчера."""

    def __init__(
        self,
        bot_token: str,
        admin_telegram_id: str,
        user_service: UserService,
        pdf_service: PdfService,
        state_storage: StateStorage,
    ) -> None:
        self.bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher(storage=state_storage)
        # Устанавливаем контекстные данные
        self.dp["user_service"] = user_service
        self.dp["pdf_service"] = pdf_service
        self.dp["admin_telegram_id"] = admin_telegram_id
        self._setup_routers()

    def _setup_routers(self) -> None:
        """Настройка роутеров с внедрением зависимостей."""
        # Передаем сервисы в хендлеры через middleware или контекст
        main_router = Router()
        main_router.message.middleware(DependencyMiddleware())
        main_router.callback_query.middleware(DependencyMiddleware())

        main_router.include_router(create_admin_router())
        self.dp.include_router(main_router)
        self.dp.include_router(create_general_lm_router())

    async def setup_commands(self) -> None:
        """Установка команд меню."""
        commands = [
            BotCommand(command="start", description="Начать работу"),
            BotCommand(command="order", description="Сделать заказ"),
        ]
        await self.bot.set_my_commands(commands)

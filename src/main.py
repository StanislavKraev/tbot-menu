import asyncio
import sys

import aiohttp
from dependency_injector.wiring import Provide, inject
from loguru import logger

from src.bot import BotInitializer
from src.config import Settings
from src.containers import AppContainer


def setup_logging(settings: Settings) -> None:
    """Настройка loguru с logfmt форматом."""
    logger.remove()

    # logfmt формат: key=value pairs
    log_format = (
        "time={time:YYYY-MM-DDTHH:mm:ss.SSSZ} " "level={level} " "logger={name} " "msg={message} " "file={file}:{line}"
    )

    logger.add(sys.stdout, format=log_format, level=settings.log_level, colorize=False)


@inject
async def run_polling(bot_initializer: BotInitializer = Provide[AppContainer.bot_initializer]) -> None:
    """Запуск в режиме polling."""
    await bot_initializer.setup_commands()
    logger.info("Starting bot in polling mode")

    await bot_initializer.dp.start_polling(bot_initializer.bot)


@inject
async def run_webhook(
    bot_initializer: BotInitializer = Provide[AppContainer.bot_initializer],
    settings: Settings = Provide[AppContainer.config],
) -> None:
    """Запуск в режиме webhook с FastAPI."""
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    from aiohttp import web

    await bot_initializer.setup_commands()
    logger.info("Starting bot in webhook mode")

    app = web.Application()

    # SimpleRequestHandler из aiogram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=bot_initializer.dp,
        bot=bot_initializer.bot,
    )
    webhook_requests_handler.register(app, path=settings.webhook_path)

    setup_application(app, bot_initializer.dp, bot=bot_initializer.bot)

    # Настройка webhook URL
    webhook_url = settings.webhook_url
    if webhook_url is not None:
        await bot_initializer.bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info(f"Webhook set to {settings.webhook_url}")

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)

    logger.info(f"Server started on {settings.webhook_host}:{settings.webhook_port}")
    await site.start()

    # Бесконечное ожидание
    while True:  # NoQA
        await asyncio.sleep(3600)


async def main() -> None:
    settings = Settings()
    setup_logging(settings)

    # Инициализация контейнера
    container = AppContainer()
    container.config.from_pydantic(settings)
    coro = container.init_resources()
    if coro:
        await coro
    container.wire(modules=[__name__])

    # HTTP клиент для сервисов
    http_session = aiohttp.ClientSession()
    container.pdf_service.add_attributes(http_client=http_session)

    try:
        if settings.bot_mode == "webhook":
            await run_webhook()
        else:
            await run_polling()
    finally:
        await http_session.close()
        coro = container.shutdown_resources()
        if coro:
            await coro


if __name__ == "__main__":
    asyncio.run(main())

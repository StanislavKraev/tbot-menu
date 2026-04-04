from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Update
from fastapi import FastAPI, Request, Response

from src.config import settings
from src.db import Database
from src.handlers import order
from src.storage.postgres import PostgresStorage

# Инициализация бота с кастомным хранилищем
storage = PostgresStorage()
bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=storage)

# Регистрация роутеров
dp.include_router(order.general_lm_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом."""
    # Startup
    await Database.connect()
    await bot.set_webhook(url=f"{settings.webhook_url}{settings.webhook_path}", drop_pending_updates=True)
    print(f"✅ Bot started with webhook: {settings.webhook_url}{settings.webhook_path}")
    yield
    # Shutdown
    await bot.delete_webhook()
    await Database.disconnect()
    print("❌ Bot stopped")


app = FastAPI(lifespan=lifespan)


@app.post(settings.webhook_path)
async def webhook(request: Request) -> Response:
    """Прием обновлений от Telegram."""
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)

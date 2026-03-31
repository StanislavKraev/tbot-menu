from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic v2 конфигурация приложения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bot
    bot_token: str
    bot_mode: Literal["webhook", "polling"] = Field(default="polling")
    admin_telegram_id: int | None = Field(default=None)

    # Webhook
    webhook_host: str = Field(default="0.0.0.0")  # NoQA: S104
    webhook_port: int = Field(default=8080)
    webhook_path: str = Field(default="/webhook")
    webhook_url: str | None = Field(default=None)
    ssl_cert_path: str | None = Field(default=None)

    # Database
    database_conn: str

    # Yandex Disk
    yandex_disk_pdf_url: str | None = Field(default=None)

    # Logging
    log_level: str = Field(default="INFO")

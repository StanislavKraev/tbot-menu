from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    webhook_url: str
    webhook_path: str = "/webhook"
    host: str = "0.0.0.0"
    port: int = 8080

    # Database
    db_url: str = "postgresql+asyncpg://bot:bot@localhost:5432/bot"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

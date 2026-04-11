from enum import Enum
from typing import Literal, Annotated

from pydantic import BaseModel, Field, HttpUrl, field_validator


class FileSourceType(str, Enum):
    S3 = "s3"
    YANDEX_DISK = "yandex_disk"
    LOCAL = "local"
    TELEGRAM = "telegram"


class BaseFileSource(BaseModel):
    """Базовый класс для всех источников файлов."""
    source_type: FileSourceType
    title: str | None = None

    class Config:
        frozen = True  # Иммутабельность
        populate_by_name = True


class S3Source(BaseFileSource):
    """Источник: AWS S3 или совместимые (MinIO, Selectel)."""
    source_type: Literal[FileSourceType.S3] = FileSourceType.S3
    bucket: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)
    region: str | None = None
    endpoint_url: HttpUrl | None = None  # Для MinIO/Selectel
    version_id: str | None = None  # Для версионированных бакетов


class YandexDiskSource(BaseFileSource):
    """Источник: Яндекс.Диск через публичную ссылку или API."""
    source_type: Literal[FileSourceType.YANDEX_DISK] = FileSourceType.YANDEX_DISK
    public_key: str  # Ключ из URL /i/XXXX
    direct_url: HttpUrl | None = None  # Кешированная прямая ссылка
    expires_at: str | None = None  # TTL прямой ссылки

    # Эти поля не попадут в БД (exclude=True), используются только в runtime
    oauth_token: str | None = Field(None, exclude=True)

    @field_validator("public_key")
    @classmethod
    def extract_key_from_url(cls, v: str) -> str:
        """Можно передавать полный URL или просто ключ."""
        if "/i/" in v:
            return v.split("/i/")[-1].split("?")[0]
        return v


class LocalStorageSource(BaseFileSource):
    """Источник: локальное хранилище на сервере."""
    source_type: Literal[FileSourceType.LOCAL] = FileSourceType.LOCAL
    path: str = Field(..., description="Относительный путь от storage root")
    filename: str
    mime_type: str = "application/pdf"
    size_bytes: int | None = None

    def get_url(self, base_url: str) -> str:
        return f"{base_url}/files/{self.path}"


class TelegramFileSource(BaseFileSource):
    """Источник: Telegram File ID (уже загружен в Telegram)."""
    source_type: Literal[FileSourceType.TELEGRAM] = FileSourceType.TELEGRAM
    file_id: str  # Для скачивания
    file_unique_id: str  # Для идентификации (постоянный)
    file_name: str | None = None

    # Не сохраняем в БД для безопасности
    bot_token: str | None = Field(None, exclude=True)


# Union с дискриминацией для автоматической десериализации
FileSource = Annotated[
    S3Source | YandexDiskSource | LocalStorageSource | TelegramFileSource,
    Field(discriminator="source_type")
]


class FileSourceWrapper(BaseModel):
    """Обертка для валидации списка источников."""
    sources: list[FileSource]


class ScenarioType(str, Enum):
    GENERAL_LEAD_MAGNIT = "general_lead_magnit"
    BACKGROUND_REMINDER = "background_reminder"


class Scenario(BaseModel):
    scenario_type: ScenarioType
    title: str | None = None
    version: int = 1

    class Config:
        frozen = True
        populate_by_name = True


class SymptomGuide(BaseModel):
    file_id: int
    symptom: str
    user_friendly_text: str     # e.g. полезный гайд / классный чеклист
    simptom_id: str


class GeneralLeadMagnitScenario(Scenario):
    scenario_type = ScenarioType.GENERAL_LEAD_MAGNIT

    guides: list[SymptomGuide] = Field(default_factory=list)


class BackgroundReminderScenario(Scenario):
    scenario_type = ScenarioType.BACKGROUND_REMINDER

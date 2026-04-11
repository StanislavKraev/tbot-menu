from psycopg2.extensions import JSON, JSONB
from sqlalchemy import Column, DateTime, MetaData, String, Table, func, Enum, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import BIGINT

from src.models.schemas import FileSourceType

metadata = MetaData()

# Таблица пользователей с оптимизированными индексами
users = Table(
    "users",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("telegram_id", BIGINT, nullable=False, unique=True),
    Column("username", String(32), nullable=True),
    Column("first_name", String(64), nullable=True),
    Column("last_name", String(64), nullable=True),
    Column("language_code", String(10), nullable=True),
    Column("utm_source", String(50), nullable=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)

# Таблица для хранения ссылки на PDF (админка)
pdf_files = Table(
    "pdf_files",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("filename", String(255), nullable=False),
    # Column("yandex_url", String(500), nullable=False),
    Column("is_active", String(1), server_default="1"), # todo: заменить на boolean
    # Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
    Column("scenario_id", BIGINT, index=True),
)

# Таблица с источниками файлов
file_sources = Table(
    "file_sources",
    metadata,
    Column("pk", BIGINT, primary_key=True, autoincrement=True),
    Column("pdf_file_id", BIGINT),
    Column("source_type", Enum(FileSourceType), nullable=False),
    Column("data", JSON(), nullable=False),  # TODO
)

# Таблица со сценариями
scenarios = Table(
    "scenarios",
    metadata,
    Column("pk", BIGINT, primary_key=True, autoincrement=True),
    Column("id", String(50), index=True, unique=True, nullable=False),
    Column("title", String(255), nullable=False),
    Column("description", String(500), nullable=False),
    Column("data", JSONB, nullable=False)
)

# Таблица с источниками файлов
file_sources = Table(
    "file_sources",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column(
        "pdf_file_id",
        BIGINT,
        ForeignKey("pdf_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    ),
    Column(
        "source_type",
        String(50),
        nullable=False,
        index=True,
        comment="Денормализованное поле для фильтрации без парсинга JSON"
    ),
    Column("sort_order", Integer, server_default="0"),  # Для ordering в UI
    Column(
        "data",
        JSONB,
        nullable=False,
        comment="Сериализованный Pydantic объект"
    ),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)
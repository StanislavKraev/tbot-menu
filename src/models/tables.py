from sqlalchemy import Column, DateTime, MetaData, String, Table, func
from sqlalchemy.dialects.postgresql import BIGINT

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
    Column("yandex_url", String(500), nullable=False),
    Column("is_active", String(1), server_default="1"),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

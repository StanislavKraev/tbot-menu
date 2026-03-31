"""Initial schema with optimized indexes

Revision ID: 001
Revises:
Create Date: 2024-03-30 21:45:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Создание таблицы users с оптимизациями для high load
    op.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            username VARCHAR(32),
            first_name VARCHAR(64),
            last_name VARCHAR(64),
            language_code VARCHAR(10),
            utm_source VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

            CONSTRAINT uq_users_telegram_id UNIQUE (telegram_id)
        );
    """)
    )

    # Covering index: покрывает запросы проверки существования без обращения к heap
    # Критично для 10+ RPS при проверке user_exists
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_users_telegram_id_covering
        ON users (telegram_id)
        INCLUDE (id, created_at);
    """)
    )

    # Partial index: только для пользователей с username (экономия 30% места)
    # WHERE clause исключает NULL значения из индекса
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_users_username_partial
        ON users (username)
        WHERE username IS NOT NULL;
    """)
    )

    # BRIN index для created_at: эффективен для временных рядов с последовательными вставками
    # pages_per_range=128 оптимален для high load с batch inserts
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_users_created_at_brin
        ON users USING BRIN (created_at)
        WITH (pages_per_range = 128);
    """)
    )

    # Комментарии для документации схемы (PostgreSQL specific)
    op.execute(
        sa.text("""
        COMMENT ON TABLE users IS 'Telegram бот пользователи с UTM tracking';
        COMMENT ON COLUMN users.telegram_id IS 'ID пользователя в Telegram (BigInt для будущего proofing)';
        COMMENT ON COLUMN users.utm_source IS 'UTM метка из /start payload';
        COMMENT ON COLUMN users.created_at IS 'Время регистрации, индекс BRIN для аналитики';
    """)
    )


def downgrade() -> None:
    # Удаление в обратном порядке (индексы удаляются автоматически с таблицей,
    # но явное удаление безопаснее для partial indexes)
    op.execute(
        sa.text("""
        DROP INDEX IF EXISTS ix_users_created_at_brin;
    """)
    )
    op.execute(
        sa.text("""
        DROP INDEX IF EXISTS ix_users_username_partial;
    """)
    )
    op.execute(
        sa.text("""
        DROP INDEX IF EXISTS ix_users_telegram_id_covering;
    """)
    )
    op.execute(
        sa.text("""
        DROP TABLE IF EXISTS users;
    """)
    )

"""Add PDF files table for admin panel

Revision ID: 002
Revises: 001
Create Date: 2024-03-30 21:46:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Таблица для хранения ссылок на Yandex Disk
    op.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS pdf_files (
            id BIGSERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            yandex_url VARCHAR(500) NOT NULL,
            is_active CHAR(1) DEFAULT '1' NOT NULL
                CONSTRAINT chk_pdf_is_active CHECK (is_active IN ('0', '1')),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    )

    # Композитный индекс для быстрого поиска активного PDF с сортировкой по дате
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_pdf_files_active_updated
        ON pdf_files (is_active, updated_at DESC);
    """)
    )

    # Триггер для автоматического обновления updated_at (PostgreSQL native)
    op.execute(
        sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    )

    op.execute(
        sa.text("""
        DROP TRIGGER IF EXISTS trg_pdf_files_updated_at ON pdf_files;
        CREATE TRIGGER trg_pdf_files_updated_at
            BEFORE UPDATE ON pdf_files
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    )

    # Комментарии
    op.execute(
        sa.text("""
        COMMENT ON TABLE pdf_files IS 'Ссылки на PDF документы на Yandex Disk';
        COMMENT ON COLUMN pdf_files.is_active IS 'Флаг активности: 1 - активен, 0 - архив';
    """)
    )

    # Seed data: базовая запись (опционально)
    op.execute(
        sa.text("""
        INSERT INTO pdf_files (filename, yandex_url, is_active)
        VALUES ('default.pdf', 'https://disk.yandex.ru/example', '1')
        ON CONFLICT DO NOTHING;
    """)
    )


def downgrade() -> None:
    op.execute(
        sa.text("""
        DROP TRIGGER IF EXISTS trg_pdf_files_updated_at ON pdf_files;
    """)
    )
    op.execute(
        sa.text("""
        DROP INDEX IF EXISTS ix_pdf_files_active_updated;
    """)
    )
    op.execute(
        sa.text("""
        DROP TABLE IF EXISTS pdf_files;
    """)
    )
    # Не удаляем функцию, т.к. она может использоваться другими таблицами

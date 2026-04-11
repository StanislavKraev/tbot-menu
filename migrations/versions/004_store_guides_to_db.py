"""store guides to DB

Revision ID: 004
Revises: 003
Create Date: 2026-04-11 16:14:09.408527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# TODO: проаверить (пока просто утащил из Kimi)
def upgrade() -> None:
    # Добавляем недостающие поля в pdf_files (если их нет в вашей 002 миграции)
    op.execute(sa.text("""
        ALTER TABLE pdf_files 
        ADD COLUMN IF NOT EXISTS title VARCHAR(255),
        ADD COLUMN IF NOT EXISTS description VARCHAR(500),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    """))

    # Создаем таблицу источников с JSONB
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS file_sources (
            id BIGSERIAL PRIMARY KEY,
            pdf_file_id BIGINT NOT NULL REFERENCES pdf_files(id) ON DELETE CASCADE,
            source_type VARCHAR(50) NOT NULL,
            display_name VARCHAR(255),
            is_primary BOOLEAN DEFAULT FALSE NOT NULL,
            sort_order INTEGER DEFAULT 0,
            data JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT uq_file_sources_primary UNIQUE (pdf_file_id, is_primary) 
                DEFERRABLE INITIALLY DEFERRED
        );
    """))

    # Индексы для производительности
    op.execute(sa.text("""
        -- Для JOIN с pdf_files
        CREATE INDEX IF NOT EXISTS ix_file_sources_pdf_file_id 
        ON file_sources(pdf_file_id);

        -- Для фильтрации по типу (S3, Yandex, etc)
        CREATE INDEX IF NOT EXISTS ix_file_sources_type 
        ON file_sources(source_type);

        -- Частичный уникальный индекс: только один primary на pdf_file_id
        CREATE UNIQUE INDEX IF NOT EXISTS ix_file_sources_primary_unique 
        ON file_sources(pdf_file_id) 
        WHERE is_primary = TRUE;

        -- GIN индекс для поиска внутри JSON (например, по bucket в S3)
        CREATE INDEX IF NOT EXISTS ix_file_sources_data_gin 
        ON file_sources USING GIN (data jsonb_path_ops);
    """))

    # Триггер автообновления updated_at
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS trg_file_sources_updated_at ON file_sources;
        CREATE TRIGGER trg_file_sources_updated_at
            BEFORE UPDATE ON file_sources
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """))

    # Комментарии для документации
    op.execute(sa.text("""
        COMMENT ON TABLE file_sources IS 
            'Полиморфное хранилище источников PDF файлов (S3, Yandex, Local, Telegram)';
        COMMENT ON COLUMN file_sources.data IS 
            'JSONB с полями конкретного источника, валидируется через Pydantic';
        COMMENT ON COLUMN file_sources.source_type IS 
            'Денормализованное поле для быстрой фильтрации без парсинга JSONB';
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_file_sources_data_gin;"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_file_sources_primary_unique;"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_file_sources_type;"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_file_sources_pdf_file_id;"))

    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_file_sources_updated_at ON file_sources;"))
    op.execute(sa.text("DROP TABLE IF EXISTS file_sources;"))

    # Убираем добавленные колонки (опционально)
    op.execute(sa.text("""
        ALTER TABLE pdf_files 
        DROP COLUMN IF EXISTS title,
        DROP COLUMN IF EXISTS description,
        DROP COLUMN IF EXISTS updated_at;
    """))
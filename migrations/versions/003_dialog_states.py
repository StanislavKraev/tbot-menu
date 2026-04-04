"""Dialog states storage

Revision ID: 003
Create Date: 2024-04-01 10:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision: str = "002"


def upgrade() -> None:
    # Таблица для хранения состояний диалогов
    op.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS dialog_states (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            chat_id BIGINT NOT NULL,
            state VARCHAR(100) NOT NULL,
            data JSONB DEFAULT '{}',
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

            CONSTRAINT uq_dialog_state_user_chat UNIQUE (user_id, chat_id)
        );
    """)
    )

    # Индекс для быстрого поиска по пользователю
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_dialog_states_lookup
        ON dialog_states (user_id, chat_id);
    """)
    )

    # BRIN для очистки старых состояний
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_dialog_states_updated_brin
        ON dialog_states USING BRIN (updated_at);
    """)
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS dialog_states;"))

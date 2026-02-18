"""metabolic copilot conversation tables

Revision ID: 20260218_0004
Revises: 20260218_0003
Create Date: 2026-02-18 00:04:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260218_0004"
down_revision: Union[str, None] = "20260218_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ai_message_role_enum = sa.Enum("user", "assistant", "system", name="ai_message_role_enum")


def upgrade() -> None:
    bind = op.get_bind()
    ai_message_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"], unique=False)

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("ai_conversations.id"), nullable=False),
        sa.Column("role", ai_message_role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"], unique=False)

    op.create_table(
        "ai_action_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("ai_conversations.id"), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_action_logs_user_id", "ai_action_logs", ["user_id"], unique=False)
    op.create_index("ix_ai_action_logs_conversation_id", "ai_action_logs", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_action_logs_conversation_id", table_name="ai_action_logs")
    op.drop_index("ix_ai_action_logs_user_id", table_name="ai_action_logs")
    op.drop_table("ai_action_logs")

    op.drop_index("ix_ai_messages_conversation_id", table_name="ai_messages")
    op.drop_table("ai_messages")

    op.drop_index("ix_ai_conversations_user_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")

    bind = op.get_bind()
    ai_message_role_enum.drop(bind, checkfirst=True)

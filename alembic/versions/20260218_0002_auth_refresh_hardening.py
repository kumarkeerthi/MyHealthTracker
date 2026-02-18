"""auth refresh hardening

Revision ID: 20260218_0002
Revises: 20260217_0001
Create Date: 2026-02-18 00:02:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260218_0002"
down_revision: Union[str, None] = "20260217_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch_op.add_column(sa.Column("last_login", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"))

    op.execute("UPDATE users SET failed_attempts = COALESCE(failed_login_attempts, 0)")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("failed_login_attempts")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("hashed_token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_hashed_token", "refresh_tokens", ["hashed_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_hashed_token", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))

    op.execute("UPDATE users SET failed_login_attempts = COALESCE(failed_attempts, 0)")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("failed_attempts")
        batch_op.drop_column("last_login")
        batch_op.drop_column("is_active")

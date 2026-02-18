"""report ingestion tables

Revision ID: 20260218_0003
Revises: 20260218_0002
Create Date: 2026-02-18 00:03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260218_0003"
down_revision: Union[str, None] = "20260218_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('report_date', sa.Date(), nullable=True),
    )
    op.create_index('ix_reports_user_id', 'reports', ['user_id'], unique=False)

    op.create_table(
        'report_parameters',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('report_id', sa.Integer(), sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('normalized_key', sa.String(length=80), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False),
        sa.Column('reference_range', sa.String(length=64), nullable=True),
    )
    op.create_index('ix_report_parameters_report_id', 'report_parameters', ['report_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_report_parameters_report_id', table_name='report_parameters')
    op.drop_table('report_parameters')
    op.drop_index('ix_reports_user_id', table_name='reports')
    op.drop_table('reports')

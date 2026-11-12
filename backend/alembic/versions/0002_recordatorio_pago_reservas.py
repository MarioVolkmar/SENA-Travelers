"""Aviso de plazo para pagar en las reservas pendientes

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12
"""
import sqlalchemy as sa

from app.database.migration_helpers import add_column_if_missing, drop_column_if_exists

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    add_column_if_missing("reservas", sa.Column("recordatorio_pago", sa.DateTime(), nullable=True))


def downgrade():
    drop_column_if_exists("reservas", "recordatorio_pago")

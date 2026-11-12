"""Detalle de los cambios en la bitácora (qué campo cambió, antes y después)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-12
"""
import sqlalchemy as sa

from app.database.migration_helpers import add_column_if_missing, drop_column_if_exists

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    add_column_if_missing("bitacora_admin", sa.Column("detalle", sa.Text(), nullable=True))


def downgrade():
    drop_column_if_exists("bitacora_admin", "detalle")

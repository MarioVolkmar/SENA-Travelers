"""Versión pequeña (miniatura) de las fotos de los paquetes

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16
"""
import sqlalchemy as sa

from app.database.migration_helpers import add_column_if_missing, drop_column_if_exists

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    add_column_if_missing("imagenes_paquetes", sa.Column("s3_key_sm", sa.String(500), nullable=True))


def downgrade():
    drop_column_if_exists("imagenes_paquetes", "s3_key_sm")

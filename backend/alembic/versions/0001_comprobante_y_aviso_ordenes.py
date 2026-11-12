"""Punto de partida: comprobante y aviso de plazo en las órdenes de pago a proveedores

Antes de Alembic, la base se creaba con database/script_BD_Travelers.sql y las migraciones
database/migracion_001 a 006. Esta es la primera migración de Alembic: agrega las columnas
que se pusieron a mano después de la 006 (si ya existen, no hace nada).

Revision ID: 0001
Revises:
Create Date: 2026-11-12
"""
import sqlalchemy as sa

from app.database.migration_helpers import add_column_if_missing, drop_column_if_exists

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    add_column_if_missing("ordenes_pago_proveedor", sa.Column("comprobante_key", sa.String(255), nullable=True))
    add_column_if_missing("ordenes_pago_proveedor", sa.Column("recordatorio_enviado", sa.DateTime(), nullable=True))


def downgrade():
    drop_column_if_exists("ordenes_pago_proveedor", "recordatorio_enviado")
    drop_column_if_exists("ordenes_pago_proveedor", "comprobante_key")

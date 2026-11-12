"""
Ayudas para escribir migraciones que se pueden aplicar más de una vez sin fallar.

Las bases que ya existían (local y producción) recibieron algunos cambios a mano antes de
usar Alembic; por eso las primeras migraciones revisan si la columna ya está antes de crearla.
"""
import sqlalchemy as sa
from alembic import op


def has_table(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def has_column(table: str, column: str) -> bool:
    if not has_table(table):
        return False
    return any(col["name"] == column for col in sa.inspect(op.get_bind()).get_columns(table))


def add_column_if_missing(table: str, column: sa.Column):
    if has_table(table) and not has_column(table, column.name):
        op.add_column(table, column)


def drop_column_if_exists(table: str, column: str):
    if has_column(table, column):
        op.drop_column(table, column)

"""
Entorno de Alembic: usa la misma conexión (.env) y los mismos modelos que la app,
así `alembic revision --autogenerate` compara los modelos con la base real.
"""
import importlib
import pkgutil
from logging.config import fileConfig

from alembic import context

import app.models
from app.database.base import Base
from app.database.connection import DATABASE_URL, engine

# Importa todos los modelos para que Base.metadata conozca todas las tablas
for module in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module.name}")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """
    Qué compara --autogenerate. La base se creó con scripts SQL cuyos índices y llaves foráneas
    tienen otros nombres, y tiene tablas que la app ya no usa: compararlas generaría migraciones
    que borran cosas. Por eso solo se comparan las tablas y columnas de los modelos.
    """
    if type_ == "table":
        return name in target_metadata.tables
    if type_ in ("index", "unique_constraint", "foreign_key_constraint"):
        return False
    return True


def run_migrations_offline():
    """Genera el SQL sin conectarse (alembic upgrade head --sql)."""
    context.configure(
        url=DATABASE_URL.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

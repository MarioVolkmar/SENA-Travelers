from sqlalchemy import Column, String

from app.database.base import Base


class SettingModel(Base):
    """Configuración del sistema editable por el administrador (clave → valor)."""
    __tablename__ = "configuraciones"

    clave = Column(String(60), primary_key=True)
    valor = Column(String(255), nullable=False)

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class AuditLogModel(Base):
    """Bitácora de acciones de los administradores: quién cambió qué y cuándo."""
    __tablename__ = "bitacora_admin"

    id_registro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True, index=True)
    usuario_nombre = Column(String(100), nullable=False)
    accion = Column(String(60), nullable=False, index=True)
    entidad = Column(String(45), nullable=False, index=True)
    entidad_id = Column(Integer, nullable=True)
    descripcion = Column(String(255), nullable=False)
    fecha = Column(DateTime, nullable=False, server_default=func.now(), index=True)

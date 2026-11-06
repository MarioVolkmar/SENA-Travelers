from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class AppNotificationModel(Base):
    """Avisos que el usuario ve en la campana de la barra de navegación."""
    __tablename__ = "notificaciones_app"

    id_notificacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(40), nullable=False)
    titulo = Column(String(120), nullable=False)
    mensaje = Column(String(255), nullable=False)
    enlace = Column(String(255), nullable=True)
    leida = Column(Boolean, nullable=False, default=False)
    fecha = Column(DateTime, nullable=False, server_default=func.now(), index=True)

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.sql import func

from app.database.base import Base

from app.models.user_model import UserModel
from app.models.reservation_model import ReservationModel

class NotificationEmailModel(Base):
    __tablename__ = "notificacion_email"

    id_notificacion_email = Column(Integer, primary_key=True, index=True, autoincrement=True)
    destinatario = Column(String(100), nullable=False)
    asunto = Column(String(100), nullable=False)
    mensaje = Column(MEDIUMTEXT, nullable=False)
    tipo_notificacion = Column(String(45), nullable=False)
    estado_envio = Column(String(45), nullable=False, default="pendiente")
    fecha_envio = Column(DateTime, nullable=False, server_default=func.now())
    usuarios_id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    reservas_id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), nullable=True)
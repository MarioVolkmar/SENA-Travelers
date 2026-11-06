from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class ReviewModel(Base):
    """Reseña de un viajero sobre un paquete. Una por reserva, después del viaje."""
    __tablename__ = "resenas"

    id_resena = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id_reserva", ondelete="CASCADE"), nullable=False, unique=True)
    paquete_id = Column(
        Integer,
        ForeignKey("paquetes_turisticos.id_paquete_turistico", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)
    calificacion = Column(Integer, nullable=False)
    comentario = Column(String(600), nullable=True)
    estado = Column(String(20), nullable=False, default="visible")  # visible | oculta
    fecha = Column(DateTime, nullable=False, server_default=func.now())

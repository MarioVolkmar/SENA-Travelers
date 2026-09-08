from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.reservation_model import ReservationModel


class PaymentModel(Base):
    __tablename__ = "pagos"

    id_pago = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    metodo_pago = Column(
        String(45),
        nullable=False
    )

    valor = Column(
        DECIMAL(10, 2),
        nullable=False
    )

    estado_pago = Column(
        String(45),
        nullable=False,
        default="aprobado"
    )

    fecha_pago = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    referencia_pago = Column(
        String(45),
        nullable=False,
        unique=True
    )

    reserva_id = Column(
        Integer,
        ForeignKey("reservas.id_reserva"),
        nullable=False
    )
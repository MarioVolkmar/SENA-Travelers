from sqlalchemy import Column, Date, ForeignKey, Integer, String

from app.database.base import Base
from app.models.reservation_model import ReservationModel


class CompanionModel(Base):
    __tablename__ = "acompanantes"

    id_acompanante = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(45), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    reserva_id = Column(Integer, ForeignKey("reservas.id_reserva"), nullable=False)
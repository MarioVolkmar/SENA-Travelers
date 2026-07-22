from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, DECIMAL, Date
from sqlalchemy.sql import func

from app.database.base import Base

class ReservationModel(Base):
    __tablename__ = "reservas"

    id_reserva = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha_compra = Column(DateTime, nullable=False, server_default=func.now())
    fecha_reserva = Column(Date, nullable=False)
    cantidad_personas = Column(Integer, nullable= False, default=1)
    cliente_id = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    id_paquete_turistico = Column(Integer, ForeignKey("paquetes_turisticos.id_paquete_turistico"), nullable=False)
    total_reserva = Column(DECIMAL(10,2), nullable= False)
    estado = Column(String(45), nullable=False, default="pendiente")
    codigo_reserva = Column(String(45), nullable=False, unique=True)
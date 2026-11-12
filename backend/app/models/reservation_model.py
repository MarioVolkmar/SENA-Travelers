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

    # Datos de la cancelación hecha por el cliente (vacíos si no se ha cancelado)
    fecha_cancelacion = Column(DateTime, nullable=True)
    penalidad_cancelacion = Column(DECIMAL(10, 2), nullable=True)
    reembolso = Column(DECIMAL(10, 2), nullable=True)

    # Cupón aplicado al reservar y recordatorio previo al viaje
    cupon_id = Column(Integer, ForeignKey("cupones.id_cupon", ondelete="SET NULL"), nullable=True)
    descuento_cupon = Column(DECIMAL(10, 2), nullable=True)
    recordatorio_enviado = Column(DateTime, nullable=True)
    # Aviso de "tu plazo para pagar está por vencer" (una sola vez por reserva)
    recordatorio_pago = Column(DateTime, nullable=True)

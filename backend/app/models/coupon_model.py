from sqlalchemy import Column, Date, DateTime, DECIMAL, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class CouponModel(Base):
    """Cupón de descuento que el viajero aplica al reservar."""
    __tablename__ = "cupones"

    id_cupon = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String(30), nullable=False, unique=True, index=True)
    descripcion = Column(String(150), nullable=True)
    tipo = Column(String(20), nullable=False)  # porcentaje | valor
    valor = Column(DECIMAL(10, 2), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    usos_maximos = Column(Integer, nullable=True)
    usos = Column(Integer, nullable=False, default=0)
    monto_minimo = Column(DECIMAL(10, 2), nullable=True)
    estado = Column(String(20), nullable=False, default="activo")
    fecha_creacion = Column(DateTime, nullable=False, server_default=func.now())

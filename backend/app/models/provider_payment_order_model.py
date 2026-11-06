from sqlalchemy import Column, Date, DateTime, DECIMAL, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.product_model import ProductModel
from app.models.provider_model import ProviderModel
from app.models.reservation_model import ReservationModel


class ProviderPaymentOrderModel(Base):
    """
    Lo que la agencia le debe a un proveedor por una reserva confirmada.
    Hay una orden por cada proveedor que presta servicios en el paquete reservado.
    """
    __tablename__ = "ordenes_pago_proveedor"

    id_orden = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String(20), nullable=False, unique=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id_proveedor"), nullable=False)
    reserva_id = Column(Integer, ForeignKey("reservas.id_reserva"), nullable=False)
    monto = Column(DECIMAL(12, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="pendiente")
    fecha_creacion = Column(DateTime, nullable=False, server_default=func.now())
    fecha_vencimiento = Column(Date, nullable=False)
    fecha_pago = Column(DateTime, nullable=True)
    referencia_pago = Column(String(60), nullable=True)
    nota = Column(String(255), nullable=True)

    detalles = relationship(
        "ProviderPaymentOrderItemModel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("proveedor_id", "reserva_id", name="uq_orden_proveedor_reserva"),
    )


class ProviderPaymentOrderItemModel(Base):
    """Línea de una orden: un producto del proveedor incluido en el paquete."""
    __tablename__ = "ordenes_pago_detalle"

    id_detalle = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(
        Integer,
        ForeignKey("ordenes_pago_proveedor.id_orden", ondelete="CASCADE"),
        nullable=False,
    )
    producto_id = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    descripcion = Column(String(150), nullable=False)
    unidad_cobro = Column(String(20), nullable=False)
    cantidad = Column(Integer, nullable=False)
    viajeros = Column(Integer, nullable=False)
    costo_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)

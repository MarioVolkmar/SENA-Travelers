from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.app_notification_service import AppNotificationService
from app.core.constants import (
    ADMIN_ROLE_ID,
    PRODUCT_UNIT_SERVICE,
    PROVIDER_ORDER_APPROVED,
    PROVIDER_ORDER_CANCELLED,
    PROVIDER_ORDER_PAID,
    PROVIDER_ORDER_PENDING,
    RESERVATION_STATUS_CONFIRMED,
)
from app.models.product_model import ProductModel
from app.models.provider_payment_order_model import (
    ProviderPaymentOrderItemModel,
    ProviderPaymentOrderModel,
)
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.tourist_package_product_model import TouristPackageProductModel
from app.models.user_model import UserModel
from app.repositories.provider_payment_order_repository import ProviderPaymentOrderRepository
from app.repositories.provider_repository import ProviderRepository
from app.services.setting_service import SettingService

OPEN_STATES = (PROVIDER_ORDER_PENDING, PROVIDER_ORDER_APPROVED)


class ProviderPaymentOrderService:
    """
    Órdenes de pago a proveedores.

    Cuando una reserva queda confirmada se genera una orden por cada proveedor
    con productos en el paquete. Monto de cada línea:
        costo del producto × cantidad incluida en el paquete × viajeros
    (los productos "por servicio" no se multiplican por viajeros).

    Flujo: pendiente → aprobada → pagada. Si la reserva se cancela, las órdenes
    que aún no se han pagado quedan anuladas.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProviderPaymentOrderRepository(db)
        self.provider_repository = ProviderRepository(db)
        self.settings = SettingService(db)

    # ---------------------------------------------------------------
    # Permisos y utilidades
    # ---------------------------------------------------------------

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_order_or_raise(self, id_orden: int):
        order = self.repository.find_by_id(id_orden)

        if order is None:
            raise LookupError("La orden de pago no existe")

        return order

    def _own_provider_or_raise(self, current_user: UserModel):
        provider = self.provider_repository.find_by_user_id(current_user.id_usuario)

        if provider is None:
            raise PermissionError("No tienes un perfil de proveedor")

        return provider

    # ---------------------------------------------------------------
    # Generación y anulación automáticas
    # ---------------------------------------------------------------

    def generate_for_reservation(self, reservation: ReservationModel):
        """Crea las órdenes de una reserva confirmada (no duplica las existentes)."""
        rows = (
            self.db.query(TouristPackageProductModel, ProductModel)
            .join(ProductModel, ProductModel.id_producto == TouristPackageProductModel.productos_id_producto)
            .filter(
                TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico
                == reservation.id_paquete_turistico
            )
            .all()
        )

        by_provider = {}
        for link, product in rows:
            by_provider.setdefault(product.proveedor_id, []).append((link, product))

        due_date = reservation.fecha_reserva + timedelta(days=self.settings.provider_payment_days())
        created = []

        for proveedor_id, items in by_provider.items():
            if self.repository.find_by_provider_and_reservation(proveedor_id, reservation.id_reserva):
                continue

            order = ProviderPaymentOrderModel(
                codigo=f"OP-{uuid4().hex[:8].upper()}",
                proveedor_id=proveedor_id,
                reserva_id=reservation.id_reserva,
                estado=PROVIDER_ORDER_PENDING,
                fecha_vencimiento=due_date,
                monto=Decimal("0"),
            )

            total = Decimal("0")

            for link, product in items:
                travelers = 1 if product.unidad_cobro == PRODUCT_UNIT_SERVICE else reservation.cantidad_personas
                subtotal = (Decimal(product.costo) * link.cantidad * travelers).quantize(Decimal("0.01"))
                total += subtotal

                order.detalles.append(ProviderPaymentOrderItemModel(
                    producto_id=product.id_producto,
                    descripcion=product.nombre[:150],
                    unidad_cobro=product.unidad_cobro,
                    cantidad=link.cantidad,
                    viajeros=travelers,
                    costo_unitario=product.costo,
                    subtotal=subtotal,
                ))

            order.monto = total
            created.append(self.repository.create(order))
            AppNotificationService(self.db).notify_provider(
                proveedor_id,
                "orden_pago",
                f"Nueva orden de pago {order.codigo}",
                f"Reserva {reservation.codigo_reserva} · ${total:,.0f}".replace(",", "."),
            )

        return created

    def cancel_for_reservation(self, reservation: ReservationModel, nota: str):
        """Anula las órdenes que aún no se han pagado (las pagadas no se tocan)."""
        cancelled = []

        for order in self.repository.list_by_reservation(reservation.id_reserva):
            if order.estado in OPEN_STATES:
                order.estado = PROVIDER_ORDER_CANCELLED
                order.nota = nota
                cancelled.append(self.repository.save(order))

        return cancelled

    def generate_missing(self, current_user: UserModel):
        """Genera las órdenes de reservas confirmadas que todavía no tienen (p. ej. anteriores a esta función)."""
        self._ensure_admin(current_user)

        reservations = (
            self.db.query(ReservationModel)
            .filter(ReservationModel.estado == RESERVATION_STATUS_CONFIRMED)
            .all()
        )

        created = []
        for reservation in reservations:
            created.extend(self.generate_for_reservation(reservation))

        return created

    # ---------------------------------------------------------------
    # Consultas
    # ---------------------------------------------------------------

    def list_orders(self, current_user: UserModel, estado=None, proveedor_id=None):
        self._ensure_admin(current_user)
        return self.repository.list_orders(estado=estado, proveedor_id=proveedor_id)

    def list_my_orders(self, current_user: UserModel, estado=None):
        provider = self._own_provider_or_raise(current_user)
        return self.repository.list_orders(estado=estado, proveedor_id=provider.id_proveedor)

    def get_order(self, id_orden: int, current_user: UserModel):
        order = self._get_order_or_raise(id_orden)

        if current_user.rol_id != ADMIN_ROLE_ID:
            provider = self._own_provider_or_raise(current_user)

            if order.proveedor_id != provider.id_proveedor:
                raise PermissionError("Solo puedes ver tus propias órdenes de pago")

        return order

    def serialize(self, order: ProviderPaymentOrderModel) -> dict:
        """Orden con los datos que se muestran en pantalla (proveedor, reserva y paquete)."""
        provider = self.provider_repository.find_by_id(order.proveedor_id)
        reservation = self.db.query(ReservationModel).filter(ReservationModel.id_reserva == order.reserva_id).first()
        package = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico == reservation.id_paquete_turistico)
            .first()
        )

        return {
            "id_orden": order.id_orden,
            "codigo": order.codigo,
            "proveedor_id": order.proveedor_id,
            "nombre_proveedor": provider.nombre_empresa if provider else f"#{order.proveedor_id}",
            "reserva_id": order.reserva_id,
            "codigo_reserva": reservation.codigo_reserva,
            "paquete": package.nombre if package else f"#{reservation.id_paquete_turistico}",
            "fecha_viaje": reservation.fecha_reserva,
            "viajeros": reservation.cantidad_personas,
            "monto": order.monto,
            "estado": order.estado,
            "fecha_creacion": order.fecha_creacion,
            "fecha_vencimiento": order.fecha_vencimiento,
            "fecha_pago": order.fecha_pago,
            "referencia_pago": order.referencia_pago,
            "nota": order.nota,
            "detalles": order.detalles,
        }

    # ---------------------------------------------------------------
    # Acciones del administrador
    # ---------------------------------------------------------------

    def approve(self, id_orden: int, current_user: UserModel):
        self._ensure_admin(current_user)
        order = self._get_order_or_raise(id_orden)

        if order.estado != PROVIDER_ORDER_PENDING:
            raise ValueError("Solo se pueden aprobar órdenes pendientes")

        order.estado = PROVIDER_ORDER_APPROVED
        return self.repository.save(order)

    def mark_paid(self, id_orden: int, referencia_pago: str, nota, current_user: UserModel):
        self._ensure_admin(current_user)
        order = self._get_order_or_raise(id_orden)

        if order.estado not in OPEN_STATES:
            raise ValueError("Solo se pueden pagar órdenes pendientes o aprobadas")

        order.estado = PROVIDER_ORDER_PAID
        order.referencia_pago = referencia_pago.strip()
        order.fecha_pago = datetime.now()

        if nota:
            order.nota = nota.strip()

        saved = self.repository.save(order)
        AppNotificationService(self.db).notify_provider(
            order.proveedor_id,
            "orden_pagada",
            f"Te pagamos la orden {order.codigo}",
            f"${order.monto:,.0f} · referencia {order.referencia_pago}".replace(",", "."),
        )
        return saved

    def annul(self, id_orden: int, nota: str, current_user: UserModel):
        self._ensure_admin(current_user)
        order = self._get_order_or_raise(id_orden)

        if order.estado not in OPEN_STATES:
            raise ValueError("Solo se pueden anular órdenes pendientes o aprobadas")

        order.estado = PROVIDER_ORDER_CANCELLED
        order.nota = nota.strip()
        return self.repository.save(order)

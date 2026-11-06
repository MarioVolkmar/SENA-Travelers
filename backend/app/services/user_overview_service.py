from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.constants import (
    ADMIN_ROLE_ID,
    PAYMENT_STATUS_APPROVED,
    PAYMENT_STATUS_PARTIALLY_REFUNDED,
    PROVIDER_ORDER_APPROVED,
    PROVIDER_ORDER_PAID,
    PROVIDER_ORDER_PENDING,
    RESERVATION_STATUS_CONFIRMED,
)
from app.models.client_model import ClientModel
from app.models.companion_model import CompanionModel
from app.models.notification_email_model import NotificationEmailModel
from app.models.payment_model import PaymentModel
from app.models.product_model import ProductModel
from app.models.provider_model import ProviderModel
from app.models.provider_payment_order_model import ProviderPaymentOrderModel
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel
from app.services.provider_payment_order_service import ProviderPaymentOrderService

RECENT_NOTIFICATIONS = 30


class UserOverviewService:
    """Ficha completa de un usuario para la consola del administrador."""

    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, id_usuario: int, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

        user = self.db.query(UserModel).filter(UserModel.id_usuario == id_usuario).first()
        if user is None:
            raise LookupError("El usuario no existe")

        client = self.db.query(ClientModel).filter(ClientModel.usuario_id == id_usuario).first()
        provider = self.db.query(ProviderModel).filter(ProviderModel.usuario_id == id_usuario).first()

        reservations, payments = self._client_activity(client)
        products, orders = self._provider_activity(provider)

        notifications = (
            self.db.query(NotificationEmailModel)
            .filter(NotificationEmailModel.usuarios_id_usuario == id_usuario)
            .order_by(NotificationEmailModel.id_notificacion_email.desc())
            .limit(RECENT_NOTIFICATIONS)
            .all()
        )

        return {
            "usuario": user,
            "cliente": client,
            "proveedor": provider,
            "reservas": reservations,
            "pagos": payments,
            "productos": products,
            "ordenes_pago": orders,
            "notificaciones": notifications,
            "resumen": self._summary(reservations, payments, products, orders),
        }

    # ---------------------------------------------------------------

    def _client_activity(self, client):
        if client is None:
            return [], []

        reservations = (
            self.db.query(ReservationModel)
            .filter(ReservationModel.cliente_id == client.id_cliente)
            .order_by(ReservationModel.id_reserva.desc())
            .all()
        )

        package_ids = {item.id_paquete_turistico for item in reservations}
        package_names = {
            package.id_paquete_turistico: package.nombre
            for package in self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico.in_(package_ids or {0}))
            .all()
        }

        reservation_ids = [item.id_reserva for item in reservations] or [0]
        companions = {}
        for companion in self.db.query(CompanionModel).filter(CompanionModel.reserva_id.in_(reservation_ids)).all():
            companions.setdefault(companion.reserva_id, []).append(companion)

        payments = (
            self.db.query(PaymentModel)
            .filter(PaymentModel.reserva_id.in_(reservation_ids))
            .order_by(PaymentModel.id_pago.desc())
            .all()
        )

        detailed = [
            {
                "id_reserva": item.id_reserva,
                "codigo_reserva": item.codigo_reserva,
                "id_paquete_turistico": item.id_paquete_turistico,
                "paquete": package_names.get(item.id_paquete_turistico, f"#{item.id_paquete_turistico}"),
                "fecha_compra": item.fecha_compra,
                "fecha_reserva": item.fecha_reserva,
                "cantidad_personas": item.cantidad_personas,
                "total_reserva": item.total_reserva,
                "estado": item.estado,
                "fecha_cancelacion": item.fecha_cancelacion,
                "penalidad_cancelacion": item.penalidad_cancelacion,
                "reembolso": item.reembolso,
                "acompanantes": companions.get(item.id_reserva, []),
            }
            for item in reservations
        ]

        return detailed, payments

    def _provider_activity(self, provider):
        if provider is None:
            return [], []

        products = (
            self.db.query(ProductModel)
            .filter(ProductModel.proveedor_id == provider.id_proveedor)
            .order_by(ProductModel.nombre.asc())
            .all()
        )

        order_service = ProviderPaymentOrderService(self.db)
        orders = [
            order_service.serialize(order)
            for order in self.db.query(ProviderPaymentOrderModel)
            .filter(ProviderPaymentOrderModel.proveedor_id == provider.id_proveedor)
            .order_by(ProviderPaymentOrderModel.id_orden.desc())
            .all()
        ]

        return products, orders

    def _summary(self, reservations, payments, products, orders):
        paid = sum(
            (Decimal(payment.valor) for payment in payments
             if payment.estado_pago in (PAYMENT_STATUS_APPROVED, PAYMENT_STATUS_PARTIALLY_REFUNDED)),
            Decimal("0"),
        )
        penalties = sum((Decimal(item["penalidad_cancelacion"] or 0) for item in reservations), Decimal("0"))

        return {
            "reservas": len(reservations),
            "reservas_confirmadas": sum(1 for item in reservations if item["estado"] == RESERVATION_STATUS_CONFIRMED),
            "total_pagado": paid,
            "penalidades": penalties,
            "productos": len(products),
            "por_cobrar": sum(
                (Decimal(order["monto"]) for order in orders
                 if order["estado"] in (PROVIDER_ORDER_PENDING, PROVIDER_ORDER_APPROVED)),
                Decimal("0"),
            ),
            "cobrado": sum(
                (Decimal(order["monto"]) for order in orders if order["estado"] == PROVIDER_ORDER_PAID),
                Decimal("0"),
            ),
        }

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.coupon_service import CouponService
from app.services.app_notification_service import AppNotificationService
from app.models.reservation_model import ReservationModel
from app.models.user_model import UserModel

from app.core import clock
from app.repositories.payment_repository import PaymentRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.tourist_package_repository import TouristPackageRepository

from app.services.companion_service import CompanionService
from app.services.notification_email_service import NotificationEmailService
from app.services.provider_payment_order_service import ProviderPaymentOrderService
from app.services.setting_service import SettingService

from app.schemas.reservation_schema import (
    ReservationCreate,
    ReservationStatusUpdate
)

from app.core.constants import (
    ADMIN_ROLE_ID,
    RESERVATION_STATUS_PENDING,
    RESERVATION_STATUS_CANCELLED,
    RESERVATION_STATUS_CONFIRMED,
    ALLOWED_RESERVATION_STATUS,
    TOURIST_PACKAGE_STATUS_ACTIVE,
    PAYMENT_STATUS_APPROVED,
    PAYMENT_STATUS_REFUNDED,
    PAYMENT_STATUS_PARTIALLY_REFUNDED,
)


class ReservationService:
    def __init__(self, db: Session):
        self.provider_orders = ProviderPaymentOrderService(db)
        self.settings = SettingService(db)
        self.app_notifications = AppNotificationService(db)
        self.coupons = CouponService(db)
        self.reservation_repository = ReservationRepository(db)
        self.payment_repository = PaymentRepository(db)
        self.client_repository = ClientRepository(db)
        self.tourist_package_repository = TouristPackageRepository(db)
        self.companion_service = CompanionService(db)
        self.notification_email_service = NotificationEmailService(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_reservation_or_raise(self, id_reserva: int):
        reservation = self.reservation_repository.find_by_id(id_reserva)

        if reservation is None:
            raise LookupError("La reserva no existe")

        return reservation

    def _get_client_profile_or_raise(self, current_user: UserModel):
        client = self.client_repository.find_by_user_id(
            current_user.id_usuario
        )

        if client is None:
            raise PermissionError("Debes tener un perfil de cliente para crear reservas")

        return client

    def _get_package_or_raise(self, id_paquete_turistico: int):
        tourist_package = self.tourist_package_repository.find_by_id(
            id_paquete_turistico
        )

        if tourist_package is None:
            raise LookupError("El paquete turístico no existe")

        return tourist_package

    def _ensure_package_is_active(self, tourist_package):
        if tourist_package.estado != TOURIST_PACKAGE_STATUS_ACTIVE:
            raise PermissionError("El paquete turístico no está disponible")

    def _ensure_reservation_date_is_valid(self, reservation_data, tourist_package):
        # Solo fechas futuras: desde mañana (el mismo día el viaje ya está en curso)
        if reservation_data.fecha_reserva <= clock.today():
            raise ValueError("La fecha de reserva debe ser a partir de mañana")

        if reservation_data.fecha_reserva < tourist_package.fecha_inicio:
            raise ValueError("La fecha de reserva no puede ser anterior al inicio del paquete")

        if reservation_data.fecha_reserva > tourist_package.fecha_fin:
            raise ValueError("La fecha de reserva no puede ser posterior al final del paquete")

    def _get_available_slots(self, tourist_package):
        reserved = self.reservation_repository.count_reserved_people(
            tourist_package.id_paquete_turistico,
            excluded_status=RESERVATION_STATUS_CANCELLED
        )

        return max(tourist_package.cupo_max - reserved, 0)

    def _ensure_package_has_capacity(self, tourist_package, cantidad_personas: int):
        available = self._get_available_slots(tourist_package)

        if cantidad_personas > available:
            raise ValueError(
                f"No hay cupo suficiente. Cupos disponibles: {available}"
            )

    def _ensure_valid_companion_count(self, reservation_data):
        if len(reservation_data.acompanantes) > reservation_data.cantidad_personas - 1:
            raise ValueError(
                "La cantidad de acompañantes no puede superar la cantidad de personas de la reserva"
            )

    def _ensure_valid_reservation_status(self, estado: str):
        if estado not in ALLOWED_RESERVATION_STATUS:
            raise ValueError("Estado de reserva no válido")

    def _ensure_owner_or_admin(
        self,
        reservation: ReservationModel,
        current_user: UserModel
    ):
        if current_user.rol_id == ADMIN_ROLE_ID:
            return

        client = self.client_repository.find_by_user_id(
            current_user.id_usuario
        )

        if client is None:
            raise PermissionError("No tienes permisos para realizar esta acción")

        if reservation.cliente_id != client.id_cliente:
            raise PermissionError("Solo puedes consultar tus propias reservas")

    def _generate_reservation_code(self):
        return f"RES-{uuid4().hex[:10].upper()}"

    def _calculate_total(self, tourist_package, cantidad_personas: int):
        precio = Decimal(tourist_package.precio)
        descuento = Decimal(tourist_package.descuento or 0)

        subtotal = precio * cantidad_personas

        if descuento > 0:
            discount_amount = subtotal * (descuento / Decimal(100))
            return subtotal - discount_amount

        return subtotal

    def create_reservation(
        self,
        reservation_data: ReservationCreate,
        current_user: UserModel
    ):
        client = self._get_client_profile_or_raise(current_user)

        tourist_package = self._get_package_or_raise(
            reservation_data.id_paquete_turistico
        )

        self._ensure_package_is_active(tourist_package)

        self._ensure_reservation_date_is_valid(
            reservation_data,
            tourist_package
        )

        # Validar antes de guardar para no dejar reservas huérfanas
        self._ensure_valid_companion_count(reservation_data)

        self._ensure_package_has_capacity(
            tourist_package,
            reservation_data.cantidad_personas
        )

        total_reserva = self._calculate_total(
            tourist_package,
            reservation_data.cantidad_personas
        )

        # Cupón de descuento (opcional): se valida antes de guardar
        coupon, coupon_discount = None, None
        if reservation_data.codigo_cupon and reservation_data.codigo_cupon.strip():
            coupon, coupon_discount = self.coupons.apply_to_total(reservation_data.codigo_cupon, Decimal(total_reserva))
            total_reserva = Decimal(total_reserva) - coupon_discount

        reservation = ReservationModel(
            fecha_reserva=reservation_data.fecha_reserva,
            cantidad_personas=reservation_data.cantidad_personas,
            cliente_id=client.id_cliente,
            id_paquete_turistico=tourist_package.id_paquete_turistico,
            total_reserva=total_reserva,
            estado=RESERVATION_STATUS_PENDING,
            codigo_reserva=self._generate_reservation_code(),
            cupon_id=coupon.id_cupon if coupon else None,
            descuento_cupon=coupon_discount
        )

        created_reservation = self.reservation_repository.create_reservation(
            reservation
        )

        if coupon is not None:
            self.coupons.register_use(coupon)

        self.companion_service.create_many_companions(
            companions_data=reservation_data.acompanantes,
            reserva_id=created_reservation.id_reserva,
            cantidad_personas=reservation_data.cantidad_personas
        )

        self.notification_email_service.create_reservation_confirmation_email(
            user=current_user,
            reservation=created_reservation
        )

        self.app_notifications.notify(
            current_user.id_usuario,
            "reserva_creada",
            f"Reserva {created_reservation.codigo_reserva} creada",
            f"{tourist_package.nombre} · {created_reservation.fecha_reserva:%d/%m/%Y}. Págala para confirmar tu cupo.",
            "/reservations",
        )

        return created_reservation

    def get_reservation_by_id(
        self,
        id_reserva: int,
        current_user: UserModel
    ):
        reservation = self._get_reservation_or_raise(id_reserva)

        self._ensure_owner_or_admin(reservation, current_user)

        return reservation

    def list_my_reservations(self, current_user: UserModel):
        client = self._get_client_profile_or_raise(current_user)

        return self.reservation_repository.list_by_client_id(
            client.id_cliente
        )

    def get_package_availability(self, id_paquete_turistico: int):
        tourist_package = self._get_package_or_raise(id_paquete_turistico)

        return {
            "id_paquete_turistico": tourist_package.id_paquete_turistico,
            "cupo_max": tourist_package.cupo_max,
            "cupos_disponibles": self._get_available_slots(tourist_package)
        }

    # ---------------------------------------------------------------
    # Cancelación por parte del cliente
    # ---------------------------------------------------------------

    def _get_own_reservation_or_raise(self, id_reserva: int, current_user: UserModel):
        client = self._get_client_profile_or_raise(current_user)
        reservation = self._get_reservation_or_raise(id_reserva)

        if reservation.cliente_id != client.id_cliente:
            raise PermissionError("Solo puedes cancelar tus propias reservas")

        return reservation

    def _cancellation_quote(self, reservation: ReservationModel):
        """
        Calcula si la reserva se puede cancelar hoy y cuánto se cobra.
        La penalidad solo aplica a lo que ya se pagó (las reservas pendientes no pagan nada).
        """
        current_day = clock.today()
        free_days = self.settings.cancellation_free_days()
        penalty_percent = self.settings.cancellation_penalty_percent()
        deadline = reservation.fecha_reserva - timedelta(days=free_days)

        payment = self.payment_repository.find_by_reservation_id(reservation.id_reserva)
        paid = (
            Decimal(payment.valor)
            if payment is not None and payment.estado_pago == PAYMENT_STATUS_APPROVED
            else Decimal("0")
        )

        motivo = None

        if reservation.estado == RESERVATION_STATUS_CANCELLED:
            motivo = "La reserva ya está cancelada"
        elif reservation.estado not in (RESERVATION_STATUS_PENDING, RESERVATION_STATUS_CONFIRMED):
            motivo = "Esta reserva no se puede cancelar"
        elif current_day >= reservation.fecha_reserva:
            motivo = "La fecha del viaje ya llegó; la reserva no se puede cancelar"

        late = current_day > deadline
        penalty = (
            (paid * Decimal(penalty_percent) / Decimal(100)).quantize(Decimal("0.01"))
            if late and paid > 0
            else Decimal("0.00")
        )

        return {
            "puede_cancelar": motivo is None,
            "motivo": motivo,
            "fecha_limite_sin_penalidad": deadline,
            "con_penalidad": penalty > 0,
            "porcentaje_penalidad": penalty_percent if late and paid > 0 else 0,
            "monto_pagado": paid.quantize(Decimal("0.01")),
            "penalidad": penalty,
            "reembolso": (paid - penalty).quantize(Decimal("0.01")),
            "payment": payment,
        }

    def get_cancellation_policy(self):
        return {
            "dias_sin_penalidad": self.settings.cancellation_free_days(),
            "porcentaje_penalidad": self.settings.cancellation_penalty_percent(),
        }

    def preview_cancellation(self, id_reserva: int, current_user: UserModel):
        reservation = self._get_own_reservation_or_raise(id_reserva, current_user)
        quote = self._cancellation_quote(reservation)
        quote.pop("payment")
        return quote

    def _refund_in_stripe(self, payment, amount, reservation: ReservationModel):
        """Reembolsa en Stripe los pagos hechos con Stripe. Los pagos simulados solo se registran."""
        from app.services.stripe_service import StripeService  # import local: evita importaciones circulares

        if StripeService.is_stripe_payment(payment) and Decimal(amount or 0) > 0:
            StripeService(self.reservation_repository.db).refund(payment, amount, reservation.codigo_reserva)

    def cancel_my_reservation(self, id_reserva: int, current_user: UserModel):
        reservation = self._get_own_reservation_or_raise(id_reserva, current_user)
        quote = self._cancellation_quote(reservation)

        if not quote["puede_cancelar"]:
            raise ValueError(quote["motivo"])

        payment = quote["payment"]

        # Si se pagó con Stripe, primero se devuelve el dinero allá; si falla, no se cancela nada
        self._refund_in_stripe(payment, quote["reembolso"], reservation)

        if payment is not None and quote["monto_pagado"] > 0:
            self.payment_repository.update_status(
                payment,
                PAYMENT_STATUS_PARTIALLY_REFUNDED if quote["con_penalidad"] else PAYMENT_STATUS_REFUNDED
            )

        cancelled = self.reservation_repository.cancel(
            reservation,
            estado=RESERVATION_STATUS_CANCELLED,
            fecha_cancelacion=datetime.now(),
            penalidad=quote["penalidad"],
            reembolso=quote["reembolso"]
        )

        self.notification_email_service.create_reservation_cancellation_email(
            user=current_user,
            reservation=cancelled
        )

        self.provider_orders.cancel_for_reservation(cancelled, "Reserva cancelada por el cliente")

        self.app_notifications.notify(
            current_user.id_usuario,
            "reserva_cancelada",
            f"Reserva {cancelled.codigo_reserva} cancelada",
            f"Reembolso: ${cancelled.reembolso or 0:,.0f}".replace(",", "."),
            "/reservations",
        )

        return cancelled

    def list_reservations(self, current_user: UserModel):
        self._ensure_admin(current_user)

        return self.reservation_repository.list_reservations()

    def _cancel_by_admin(self, reservation: ReservationModel):
        """
        Cancelación decidida por Travelers: no hay penalidad para el cliente,
        se reembolsa todo lo pagado y se anulan las órdenes a proveedores.
        """
        payment = self.payment_repository.find_by_reservation_id(reservation.id_reserva)
        paid = Decimal("0.00")

        if payment is not None and payment.estado_pago == PAYMENT_STATUS_APPROVED:
            paid = Decimal(payment.valor).quantize(Decimal("0.01"))
            self._refund_in_stripe(payment, paid, reservation)
            self.payment_repository.update_status(payment, PAYMENT_STATUS_REFUNDED)

        cancelled = self.reservation_repository.cancel(
            reservation,
            estado=RESERVATION_STATUS_CANCELLED,
            fecha_cancelacion=datetime.now(),
            penalidad=Decimal("0.00"),
            reembolso=paid
        )

        client = self.client_repository.find_by_id(cancelled.cliente_id)
        user = (
            self.reservation_repository.db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first()
            if client is not None
            else None
        )

        if user is not None:
            self.notification_email_service.create_reservation_cancellation_email(
                user=user,
                reservation=cancelled,
                by_admin=True
            )

        self.provider_orders.cancel_for_reservation(cancelled, "Reserva cancelada por el administrador")

        self.app_notifications.notify_client(
            cancelled.cliente_id,
            "reserva_cancelada",
            f"Travelers canceló tu reserva {cancelled.codigo_reserva}",
            f"Sin penalidad. Reembolso: ${paid:,.0f}".replace(",", "."),
        )

        return cancelled

    def update_reservation_status(
        self,
        id_reserva: int,
        status_data: ReservationStatusUpdate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        reservation = self._get_reservation_or_raise(id_reserva)

        self._ensure_valid_reservation_status(status_data.estado)

        # Una reserva cancelada ya liquidó reembolsos y anuló órdenes: no se reactiva
        if reservation.estado == RESERVATION_STATUS_CANCELLED and status_data.estado != RESERVATION_STATUS_CANCELLED:
            raise ValueError("Una reserva cancelada no se puede volver a confirmar ni dejar pendiente")

        if status_data.estado == RESERVATION_STATUS_CANCELLED and reservation.estado != RESERVATION_STATUS_CANCELLED:
            return self._cancel_by_admin(reservation)

        updated = self.reservation_repository.update_status(
            reservation,
            status_data.estado
        )

        # Mantiene las órdenes de pago a proveedores al día con el estado de la reserva
        if updated.estado == RESERVATION_STATUS_CONFIRMED:
            self.provider_orders.generate_for_reservation(updated)
            self.app_notifications.notify_client(
                updated.cliente_id,
                "reserva_confirmada",
                f"Reserva {updated.codigo_reserva} confirmada",
                "Tu viaje está confirmado. Descarga tu voucher desde Mis reservas.",
            )
        elif updated.estado == RESERVATION_STATUS_CANCELLED:
            self.provider_orders.cancel_for_reservation(updated, "Reserva cancelada por el administrador")

        return updated
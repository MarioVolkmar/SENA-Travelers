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
    MIN_COMPANION_AGE,
    PAYMENT_REMINDER_HOURS_BEFORE,
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

    def _ensure_companions_meet_min_age(self, reservation_data):
        """Cada acompañante debe tener al menos 7 años cumplidos el día del viaje."""
        for companion in reservation_data.acompanantes:
            if companion.fecha_nacimiento > clock.today():
                raise ValueError(f"La fecha de nacimiento de {companion.nombre} no puede ser futura")
            if clock.age_on(companion.fecha_nacimiento, reservation_data.fecha_reserva) < MIN_COMPANION_AGE:
                raise ValueError(
                    f"{companion.nombre} debe tener al menos {MIN_COMPANION_AGE} años el día del viaje"
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
        self._ensure_companions_meet_min_age(reservation_data)

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
            reservation=created_reservation,
            payment_hours=self.settings.payment_hours()
        )

        self.app_notifications.notify(
            current_user.id_usuario,
            "reserva_creada",
            f"Reserva {created_reservation.codigo_reserva} creada",
            f"{tourist_package.nombre} · {created_reservation.fecha_reserva:%d/%m/%Y}. Págala para confirmar tu cupo.",
            "/reservations",
        )

        return self._with_deadline(created_reservation)

    def get_reservation_by_id(
        self,
        id_reserva: int,
        current_user: UserModel
    ):
        reservation = self._get_reservation_or_raise(id_reserva)

        self._ensure_owner_or_admin(reservation, current_user)

        return self._with_deadline(reservation)

    def list_my_reservations(self, current_user: UserModel):
        client = self._get_client_profile_or_raise(current_user)

        return self._with_deadlines(self.reservation_repository.list_by_client_id(
            client.id_cliente
        ))

    # ---------------------------------------------------------------
    # Plazo para pagar las reservas pendientes
    # ---------------------------------------------------------------

    def payment_deadline(self, reservation: ReservationModel, hours: int | None = None):
        """Fecha y hora límite para pagar (hora del servidor, sin zona). None si no está pendiente."""
        if reservation.estado != RESERVATION_STATUS_PENDING or reservation.fecha_compra is None:
            return None
        return reservation.fecha_compra + timedelta(hours=hours or self.settings.payment_hours())

    def _with_deadlines(self, reservations):
        hours = self.settings.payment_hours()
        for reservation in reservations:
            deadline = self.payment_deadline(reservation, hours)
            # .astimezone() le pone la zona del servidor: el navegador la muestra en la hora local del viajero
            reservation.vence_pago = deadline.astimezone() if deadline else None
        return reservations

    def _with_deadline(self, reservation: ReservationModel):
        return self._with_deadlines([reservation])[0]

    def ensure_payable_in_time(self, reservation: ReservationModel):
        """Antes de empezar un pago: si ya pasó el plazo, no se deja pagar (el sistema la cancelará)."""
        deadline = self.payment_deadline(reservation)
        if deadline is not None and deadline <= datetime.now():
            raise ValueError(
                "Se venció el plazo para pagar esta reserva. Puedes reservar de nuevo mientras haya cupos."
            )

    @staticmethod
    def is_expired_cancellation(reservation: ReservationModel) -> bool:
        """Las vencidas se cancelan sin penalidad ni reembolso registrados (vacíos, no en cero)."""
        return (
            reservation.estado == RESERVATION_STATUS_CANCELLED
            and reservation.fecha_cancelacion is not None
            and reservation.penalidad_cancelacion is None
            and reservation.reembolso is None
        )

    def expire_unpaid_reservations(self, now: datetime | None = None) -> int:
        """
        Cancela las reservas pendientes cuyo plazo de pago ya pasó y libera sus cupos.
        Avisa al viajero por correo y en la campana. Devuelve cuántas se cancelaron.
        """
        now = now or datetime.now()
        limit = now - timedelta(hours=self.settings.payment_hours())
        db = self.reservation_repository.db
        overdue = (
            db.query(ReservationModel)
            .filter(
                ReservationModel.estado == RESERVATION_STATUS_PENDING,
                ReservationModel.fecha_compra <= limit,
            )
            .all()
        )

        expired = 0
        for reservation in overdue:
            if self.payment_repository.find_by_reservation_id(reservation.id_reserva) is not None:
                continue  # tiene un pago registrado: no se toca

            cancelled = self.reservation_repository.cancel(
                reservation,
                estado=RESERVATION_STATUS_CANCELLED,
                fecha_cancelacion=now,
                penalidad=None,
                reembolso=None,
            )
            expired += 1

            client = self.client_repository.find_by_id(cancelled.cliente_id)
            user = (
                db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first()
                if client is not None
                else None
            )
            if user is not None:
                try:
                    self.notification_email_service.create_reservation_cancellation_email(
                        user=user, reservation=cancelled, expired=True
                    )
                except Exception:  # un correo que falla no detiene las demás cancelaciones
                    pass

            self.app_notifications.notify_client(
                cancelled.cliente_id,
                "reserva_cancelada",
                f"Reserva {cancelled.codigo_reserva} vencida",
                "No se pagó a tiempo y se canceló automáticamente. Puedes reservar de nuevo si hay cupos.",
                "/reservations",
            )

        return expired

    @staticmethod
    def payment_reminder_lead(hours: int) -> float:
        """Cuántas horas antes del vencimiento se avisa: 4, o la mitad del plazo si es más corto."""
        return min(PAYMENT_REMINDER_HOURS_BEFORE, hours / 2)

    def remind_unpaid_reservations(self, now: datetime | None = None) -> int:
        """
        Avisa (correo y campana) a quien tiene una reserva pendiente cuyo plazo para pagar está por vencer.
        Se envía una sola vez por reserva. Devuelve cuántos avisos se enviaron.
        """
        now = now or datetime.now()
        hours = self.settings.payment_hours()
        lead = self.payment_reminder_lead(hours)
        db = self.reservation_repository.db
        due = (
            db.query(ReservationModel)
            .filter(
                ReservationModel.estado == RESERVATION_STATUS_PENDING,
                ReservationModel.recordatorio_pago.is_(None),
                ReservationModel.fecha_compra <= now - timedelta(hours=hours - lead),
                ReservationModel.fecha_compra > now - timedelta(hours=hours),  # las ya vencidas no se avisan
            )
            .all()
        )

        reminded = 0
        for reservation in due:
            if self.payment_repository.find_by_reservation_id(reservation.id_reserva) is not None:
                continue
            reservation.recordatorio_pago = now
            db.commit()
            reminded += 1

            left = self.payment_deadline(reservation, hours) - now
            hours_left = int(left.total_seconds() // 3600)
            cuando = "menos de una hora" if hours_left < 1 else f"{hours_left} {'hora' if hours_left == 1 else 'horas'}"

            client = self.client_repository.find_by_id(reservation.cliente_id)
            user = (
                db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first()
                if client is not None
                else None
            )
            if user is not None:
                try:
                    self.notification_email_service.create_payment_reminder_email(
                        user=user, reservation=reservation, hours_left=hours_left
                    )
                except Exception:  # un correo que falla no detiene los demás avisos
                    pass

            self.app_notifications.notify_client(
                reservation.cliente_id,
                "recordatorio_pago",
                f"Reserva {reservation.codigo_reserva} por vencer",
                f"Te quedan {cuando} para pagarla. Si no, se cancela sola y el cupo queda libre.",
                "/reservations",
            )

        return reminded

    def reactivate_expired(self, reservation: ReservationModel) -> bool:
        """
        Si un pago llega justo después de vencer la reserva (por ejemplo, Stripe tardó),
        la reserva vuelve a quedar pendiente para registrar el pago, siempre que aún haya cupo.
        """
        if not self.is_expired_cancellation(reservation):
            return False
        package = self.tourist_package_repository.find_by_id(reservation.id_paquete_turistico)
        if package is None or self._get_available_slots(package) < reservation.cantidad_personas:
            return False

        reservation.estado = RESERVATION_STATUS_PENDING
        reservation.fecha_cancelacion = None
        self.reservation_repository.db.commit()
        self.reservation_repository.db.refresh(reservation)
        return True

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
            "horas_para_pagar": self.settings.payment_hours(),
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

    def admin_detail(self, id_reserva: int, current_user: UserModel) -> dict:
        """
        Todo lo de una reserva para su ficha en la consola: viajero, acompañantes,
        paquete, pago (con IVA) y órdenes a proveedores.
        """
        from app.core.taxes import split_iva
        from app.models.companion_model import CompanionModel

        self._ensure_admin(current_user)
        reservation = self._with_deadline(self._get_reservation_or_raise(id_reserva))
        db = self.reservation_repository.db

        client = self.client_repository.find_by_id(reservation.cliente_id)
        user = (
            db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first()
            if client is not None else None
        )
        package = self.tourist_package_repository.find_by_id(reservation.id_paquete_turistico)
        companions = (
            db.query(CompanionModel).filter(CompanionModel.reserva_id == reservation.id_reserva).all()
        )
        payment = self.payment_repository.find_by_reservation_id(reservation.id_reserva)
        orders = self.provider_orders.repository.list_by_reservation(reservation.id_reserva)
        base, iva = split_iva(reservation.total_reserva)

        return {
            "reserva": {
                "id_reserva": reservation.id_reserva,
                "codigo_reserva": reservation.codigo_reserva,
                "estado": reservation.estado,
                "fecha_compra": reservation.fecha_compra,
                "fecha_reserva": reservation.fecha_reserva,
                "cantidad_personas": reservation.cantidad_personas,
                "total_reserva": reservation.total_reserva,
                "subtotal_sin_iva": base,
                "iva": iva,
                "descuento_cupon": reservation.descuento_cupon,
                "fecha_cancelacion": reservation.fecha_cancelacion,
                "penalidad_cancelacion": reservation.penalidad_cancelacion,
                "reembolso": reservation.reembolso,
                "vence_pago": reservation.vence_pago,
                "vencida": self.is_expired_cancellation(reservation),
            },
            "viajero": {
                "id_usuario": user.id_usuario if user else None,
                "nombre": user.nombre if user else None,
                "email": user.email if user else None,
                "foto_url": getattr(user, "foto_url", None) if user else None,
                "identificacion": client.identificacion if client else None,
                "fecha_nacimiento": client.fecha_nacimiento if client else None,
            },
            "acompanantes": [
                {"nombre": item.nombre, "documento": item.documento, "fecha_nacimiento": item.fecha_nacimiento}
                for item in companions
            ],
            "paquete": {
                "id_paquete_turistico": package.id_paquete_turistico,
                "nombre": package.nombre,
                "estado": package.estado,
            } if package else None,
            "pago": {
                "id_pago": payment.id_pago,
                "referencia_pago": payment.referencia_pago,
                "metodo_pago": payment.metodo_pago,
                "valor": payment.valor,
                "estado_pago": payment.estado_pago,
                "fecha_pago": payment.fecha_pago,
            } if payment else None,
            "ordenes": [self.provider_orders.serialize(order) for order in orders],
        }

    def list_reservations(self, current_user: UserModel):
        self._ensure_admin(current_user)

        return self._with_deadlines(self.reservation_repository.list_reservations())

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
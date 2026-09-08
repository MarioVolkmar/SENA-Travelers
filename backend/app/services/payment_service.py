from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.payment_model import PaymentModel
from app.models.reservation_model import ReservationModel
from app.models.user_model import UserModel

from app.repositories.payment_repository import PaymentRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.client_repository import ClientRepository
from app.services.notification_email_service import NotificationEmailService

from app.schemas.payment_schema import PaymentCreate

from app.core.constants import (
    ADMIN_ROLE_ID,
    PAYMENT_STATUS_APPROVED,
    RESERVATION_STATUS_PENDING,
    RESERVATION_STATUS_CONFIRMED,
)


class PaymentService:
    def __init__(self, db: Session):
        self.payment_repository = PaymentRepository(db)
        self.reservation_repository = ReservationRepository(db)
        self.client_repository = ClientRepository(db)
        self.notification_email_service = NotificationEmailService(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_client_profile_or_raise(self, current_user: UserModel):
        client = self.client_repository.find_by_user_id(
            current_user.id_usuario
        )

        if client is None:
            raise PermissionError("Debes tener un perfil de cliente para realizar pagos")

        return client

    def _get_reservation_or_raise(self, reserva_id: int):
        reservation = self.reservation_repository.find_by_id(reserva_id)

        if reservation is None:
            raise LookupError("La reserva no existe")

        return reservation

    def _ensure_reservation_belongs_to_client(
        self,
        reservation: ReservationModel,
        cliente_id: int
    ):
        if reservation.cliente_id != cliente_id:
            raise PermissionError("Solo puedes pagar tus propias reservas")

    def _ensure_reservation_is_pending(self, reservation: ReservationModel):
        if reservation.estado != RESERVATION_STATUS_PENDING:
            raise ValueError("Solo se pueden pagar reservas pendientes")

    def _ensure_reservation_has_no_payment(self, reserva_id: int):
        existing_payment = self.payment_repository.find_by_reservation_id(
            reserva_id
        )

        if existing_payment is not None:
            raise ValueError("La reserva ya tiene un pago registrado")

    def _ensure_payment_value_matches_reservation(
        self,
        payment_value: Decimal,
        reservation_total: Decimal
    ):
        if Decimal(payment_value) != Decimal(reservation_total):
            raise ValueError("El valor del pago no coincide con el total de la reserva")

    def _generate_payment_reference(self):
        return f"PAY-{uuid4().hex[:10].upper()}"

    def create_payment(
            self,
            payment_data: PaymentCreate,
            current_user: UserModel
        ):
        client = self._get_client_profile_or_raise(current_user)

        reservation = self._get_reservation_or_raise(
            payment_data.reserva_id
        )

        self._ensure_reservation_belongs_to_client(
            reservation,
            client.id_cliente
        )

        self._ensure_reservation_is_pending(reservation)

        self._ensure_reservation_has_no_payment(
            reservation.id_reserva
        )

        self._ensure_payment_value_matches_reservation(
            payment_data.valor,
            reservation.total_reserva
        )

        payment = PaymentModel(
            metodo_pago=payment_data.metodo_pago,
            valor=payment_data.valor,
            estado_pago=PAYMENT_STATUS_APPROVED,
            referencia_pago=self._generate_payment_reference(),
            reserva_id=reservation.id_reserva
        )

        created_payment = self.payment_repository.create_payment(payment)

        updated_reservation = self.reservation_repository.update_status(
            reservation,
            RESERVATION_STATUS_CONFIRMED
        )

        self.notification_email_service.create_payment_confirmation_email(
            user=current_user,
            reservation=updated_reservation,
            payment=created_payment
        )

        return created_payment

    def get_payment_by_id(
        self,
        id_pago: int,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        payment = self.payment_repository.find_by_id(id_pago)

        if payment is None:
            raise LookupError("El pago no existe")

        return payment

    def list_payments(self, current_user: UserModel):
        self._ensure_admin(current_user)

        return self.payment_repository.list_payments()

    def list_my_payments(self, current_user: UserModel):
        client = self._get_client_profile_or_raise(current_user)

        return self.payment_repository.list_by_client_id(
            client.id_cliente
        )
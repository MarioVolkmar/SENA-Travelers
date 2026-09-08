from sqlalchemy.orm import Session

from app.models.notification_email_model import NotificationEmailModel
from app.models.user_model import UserModel
from app.models.reservation_model import ReservationModel
from app.models.payment_model import PaymentModel

from app.repositories.notification_email_repository import NotificationEmailRepository

from app.core.constants import (
    ADMIN_ROLE_ID,
    NOTIFICATION_TYPE_EMAIL_VERIFICATION,
    NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
    NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
    EMAIL_STATUS_SENT_SIMULATED
)


class NotificationEmailService:
    def __init__(self, db: Session):
        self.notification_email_repository = NotificationEmailRepository(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_notification_or_raise(self, id_notificacion_email: int):
        notification = self.notification_email_repository.find_by_id(
            id_notificacion_email
        )

        if notification is None:
            raise LookupError("La notificación no existe")

        return notification

    def _ensure_valid_user_for_notification(self, user: UserModel):
        if user is None:
            raise ValueError("Usuario inválido")

        if user.id_usuario is None:
            raise ValueError("El usuario no tiene id asignado")

        if not user.email:
            raise ValueError("El usuario no tiene email")

    def create_verification_email(
        self,
        user: UserModel,
        verification_link: str
    ):
        self._ensure_valid_user_for_notification(user)

        email = NotificationEmailModel(
            destinatario=user.email,
            asunto="Verifica tu cuenta Travelers",
            mensaje=(
                f"Hola {user.nombre}, verifica tu cuenta en Travelers "
                f"usando este enlace: {verification_link}"
            ),
            tipo_notificacion=NOTIFICATION_TYPE_EMAIL_VERIFICATION,
            estado_envio=EMAIL_STATUS_SENT_SIMULATED,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=None
        )

        return self.notification_email_repository.create_notification_email(
            email
        )

    def create_reservation_confirmation_email(
        self,
        user: UserModel,
        reservation: ReservationModel
    ):
        self._ensure_valid_user_for_notification(user)

        if reservation is None:
            raise ValueError("Reserva inválida")

        if reservation.id_reserva is None:
            raise ValueError("La reserva no tiene id asignado")

        email = NotificationEmailModel(
            destinatario=user.email,
            asunto="Confirmación de reserva - Travelers",
            mensaje=(
                f"Hola {user.nombre}, tu reserva fue creada correctamente. "
                f"Código de reserva: {reservation.codigo_reserva}. "
                f"Estado actual: {reservation.estado}. "
                f"Total: {reservation.total_reserva}."
            ),
            tipo_notificacion=NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
            estado_envio=EMAIL_STATUS_SENT_SIMULATED,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reservation.id_reserva
        )

        return self.notification_email_repository.create_notification_email(
            email
        )

    def create_payment_confirmation_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        payment: PaymentModel
    ):
        self._ensure_valid_user_for_notification(user)

        if reservation is None:
            raise ValueError("Reserva inválida")

        if reservation.id_reserva is None:
            raise ValueError("La reserva no tiene id asignado")

        if payment is None:
            raise ValueError("Pago inválido")

        if payment.id_pago is None:
            raise ValueError("El pago no tiene id asignado")

        email = NotificationEmailModel(
            destinatario=user.email,
            asunto="Confirmación de pago - Travelers",
            mensaje=(
                f"Hola {user.nombre}, tu pago fue aprobado correctamente. "
                f"Referencia de pago: {payment.referencia_pago}. "
                f"Código de reserva: {reservation.codigo_reserva}. "
                f"Estado de la reserva: {reservation.estado}. "
                f"Valor pagado: {payment.valor}."
            ),
            tipo_notificacion=NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
            estado_envio=EMAIL_STATUS_SENT_SIMULATED,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reservation.id_reserva
        )

        return self.notification_email_repository.create_notification_email(
            email
        )

    def get_notification_by_id(
        self,
        id_notificacion_email: int,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        return self._get_notification_or_raise(id_notificacion_email)

    def list_notifications(self, current_user: UserModel):
        self._ensure_admin(current_user)

        return self.notification_email_repository.list_notifications()

    def list_my_notifications(self, current_user: UserModel):
        return self.notification_email_repository.list_by_user_id(
            current_user.id_usuario
        )

    def list_notifications_by_reservation(
        self,
        reserva_id: int,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        return self.notification_email_repository.list_by_reservation_id(
            reserva_id
        )
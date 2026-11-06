import os
from sqlalchemy.orm import Session

from app.models.notification_email_model import NotificationEmailModel
from app.models.user_model import UserModel
from app.models.reservation_model import ReservationModel
from app.models.payment_model import PaymentModel

from app.repositories.notification_email_repository import NotificationEmailRepository

from app.services.email_sender_service import EmailSenderService

from app.core.constants import (
    ADMIN_ROLE_ID,
    NOTIFICATION_TYPE_EMAIL_VERIFICATION,
    NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
    NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
    NOTIFICATION_TYPE_PASSWORD_RESET,
    NOTIFICATION_TYPE_RESERVATION_CANCELLATION,
    NOTIFICATION_TYPE_TRIP_REMINDER,
    EMAIL_STATUS_SENT,
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_DISABLED
)


class NotificationEmailService:
    def __init__(self, db: Session):
        self.notification_email_repository = NotificationEmailRepository(db)
        self.email_sender_service = EmailSenderService()

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

    def _send_and_save_notification(
        self,
        destinatario: str,
        asunto: str,
        mensaje: str,
        tipo_notificacion: str,
        usuarios_id_usuario: int,
        reservas_id_reserva: int | None = None
    ):
        try:
            sent = self.email_sender_service.send_email(
                to_email=destinatario,
                subject=asunto,
                message=mensaje
            )

            estado_envio = EMAIL_STATUS_SENT if sent else EMAIL_STATUS_DISABLED

        except Exception:
            estado_envio = EMAIL_STATUS_FAILED

        email = NotificationEmailModel(
            destinatario=destinatario,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=tipo_notificacion,
            estado_envio=estado_envio,
            usuarios_id_usuario=usuarios_id_usuario,
            reservas_id_reserva=reservas_id_reserva
        )

        return self.notification_email_repository.create_notification_email(
            email
        )

    def create_verification_email(
        self,
        user: UserModel,
        verification_link: str
    ):
        self._ensure_valid_user_for_notification(user)

        asunto = "Verifica tu cuenta Travelers"

        mensaje = (
            f"Hola {user.nombre},\n\n"
            f"Gracias por registrarte en Travelers.\n\n"
            f"Para verificar tu cuenta, abre el siguiente enlace:\n"
            f"{verification_link}\n\n"
            f"Si no creaste esta cuenta, puedes ignorar este mensaje."
        )

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=NOTIFICATION_TYPE_EMAIL_VERIFICATION,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=None
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

        asunto = "Confirmación de reserva - Travelers"

        mensaje = (
            f"Hola {user.nombre},\n\n"
            f"Tu reserva fue creada correctamente.\n\n"
            f"Código de reserva: {reservation.codigo_reserva}\n"
            f"Estado actual: {reservation.estado}\n"
            f"Fecha de reserva: {reservation.fecha_reserva}\n"
            f"Cantidad de personas: {reservation.cantidad_personas}\n"
            f"Total: {reservation.total_reserva}\n\n"
            f"Gracias por confiar en Travelers."
        )

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reservation.id_reserva
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

        asunto = "Confirmación de pago - Travelers"

        mensaje = (
            f"Hola {user.nombre},\n\n"
            f"Tu pago fue aprobado correctamente.\n\n"
            f"Referencia de pago: {payment.referencia_pago}\n"
            f"Código de reserva: {reservation.codigo_reserva}\n"
            f"Estado de la reserva: {reservation.estado}\n"
            f"Método de pago: {payment.metodo_pago}\n"
            f"Valor pagado: {payment.valor}\n\n"
            f"Gracias por viajar con Travelers."
        )

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reservation.id_reserva
        )

    def create_reservation_cancellation_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        by_admin: bool = False
    ):
        self._ensure_valid_user_for_notification(user)

        if reservation is None or reservation.id_reserva is None:
            raise ValueError("Reserva inválida")

        penalidad = reservation.penalidad_cancelacion or 0
        reembolso = reservation.reembolso or 0

        if by_admin:
            detalle = "La cancelación la realizó Travelers, así que no tiene penalidad.\n" + (
                f"Se reembolsa el valor completo de {reembolso}.\n"
                if reembolso > 0
                else "La reserva no tenía pagos registrados.\n"
            )
        elif reembolso > 0 and penalidad > 0:
            detalle = (
                f"Como cancelaste después del plazo sin penalidad, se aplicó una penalidad de {penalidad}.\n"
                f"Valor a reembolsar: {reembolso}\n"
            )
        elif reembolso > 0:
            detalle = f"Cancelaste dentro del plazo: se reembolsa el valor completo de {reembolso}.\n"
        else:
            detalle = "La reserva no tenía pagos registrados, así que no hay cobros ni reembolsos.\n"

        mensaje = (
            f"Hola {user.nombre},\n\n"
            f"Tu reserva {reservation.codigo_reserva} fue cancelada.\n\n"
            f"{detalle}\n"
            f"Esperamos verte pronto en Travelers."
        )

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto="Cancelación de reserva - Travelers",
            mensaje=mensaje,
            tipo_notificacion=NOTIFICATION_TYPE_RESERVATION_CANCELLATION,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reservation.id_reserva
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

    def create_password_reset_email(
        self,
        user: UserModel,
        reset_link: str
    ):
        self._ensure_valid_user_for_notification(user)

        asunto = "Recuperación de contraseña - Travelers"

        mensaje = (
            f"Hola {user.nombre},\n\n"
            f"Recibimos una solicitud para restablecer tu contraseña.\n\n"
            f"Para crear una nueva contraseña, abre el siguiente enlace:\n"
            f"{reset_link}\n\n"
            f"Este enlace es temporal. Si no solicitaste este cambio, "
            f"puedes ignorar este mensaje."
        )

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=NOTIFICATION_TYPE_PASSWORD_RESET,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=None
        )
    def create_trip_reminder_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        package_name: str,
        days_left: int
    ):
        self._ensure_valid_user_for_notification(user)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        cuando = "mañana" if days_left == 1 else f"en {days_left} días"

        asunto = f"Tu viaje es {cuando} - Travelers"

        mensaje = (
            f"Hola {user.nombre},\n\n"
            f"¡Ya casi! Tu viaje «{package_name}» es {cuando}, "
            f"el {reservation.fecha_reserva:%d/%m/%Y}.\n\n"
            f"Código de reserva: {reservation.codigo_reserva}\n"
            f"Viajeros: {reservation.cantidad_personas}\n\n"
            f"Descarga tu voucher con código QR desde Mis reservas:\n"
            f"{frontend_url}/reservations\n\n"
            f"Lleva tu documento de identidad. ¡Buen viaje!\n"
            f"Equipo Travelers"
        )

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=NOTIFICATION_TYPE_TRIP_REMINDER,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reservation.id_reserva
        )

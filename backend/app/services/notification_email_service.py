import os
from sqlalchemy.orm import Session

from app.models.notification_email_model import NotificationEmailModel
from app.models.user_model import UserModel
from app.models.reservation_model import ReservationModel
from app.models.payment_model import PaymentModel
from app.models.tourist_package_model import TouristPackageModel

from app.repositories.notification_email_repository import NotificationEmailRepository

from app.services.email_sender_service import EmailSenderService
from app.services.email_templates import render_email
from app.services.voucher_service import long_date, money as voucher_money
from app.core.taxes import split_iva

from app.core.constants import (
    ADMIN_ROLE_ID,
    IVA_PERCENT,
    NOTIFICATION_TYPE_EMAIL_VERIFICATION,
    NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
    NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
    NOTIFICATION_TYPE_PASSWORD_RESET,
    NOTIFICATION_TYPE_RESERVATION_CANCELLATION,
    NOTIFICATION_TYPE_TRIP_REMINDER,
    NOTIFICATION_TYPE_PAYMENT_REMINDER,
    EMAIL_STATUS_SENT,
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_DISABLED
)


def money(value) -> str:
    """"$ 750.000" con espacio que no se parte: el signo nunca queda solo al final de una línea."""
    return voucher_money(value).replace(" ", " ")


def frontend_url():
    return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def people_label(count: int) -> str:
    return f"{count} {'persona' if count == 1 else 'personas'}"


def text_version(greeting: str, paragraphs: list[str], details=None, link=None, note=""):
    """Versión en texto plano del correo (la que se guarda en la base y ven los clientes sin HTML)."""
    parts = [greeting, "", *[f"{paragraph}\n" for paragraph in paragraphs]]
    if details:
        parts += [f"{label}: {value}" for label, value in details] + [""]
    if link:
        parts += [link, ""]
    if note:
        parts += [note, ""]
    parts.append("Equipo Travelers")
    return "\n".join(parts)


class NotificationEmailService:
    def __init__(self, db: Session):
        self.db = db
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

    def _package_name(self, reservation: ReservationModel) -> str:
        package = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico == reservation.id_paquete_turistico)
            .first()
        )
        return package.nombre if package else "tu paquete"

    def _send_and_save_notification(
        self,
        destinatario: str,
        asunto: str,
        mensaje: str,
        tipo_notificacion: str,
        usuarios_id_usuario: int,
        reservas_id_reserva: int | None = None,
        html: str | None = None
    ):
        try:
            sent = self.email_sender_service.send_email(
                to_email=destinatario,
                subject=asunto,
                message=mensaje,
                html=html
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

    def _build_and_send(self, *, user, asunto, tipo, reserva_id=None, **content):
        """Arma las dos versiones (HTML y texto) con el mismo contenido y envía el correo."""
        greeting = content["greeting"]
        paragraphs = content["paragraphs"]
        details = content.get("details")
        button = content.get("button")
        note = content.get("note", "")

        html = render_email(**content)
        mensaje = text_version(greeting, paragraphs, details, button[1] if button else None, note)

        return self._send_and_save_notification(
            destinatario=user.email,
            asunto=asunto,
            mensaje=mensaje,
            tipo_notificacion=tipo,
            usuarios_id_usuario=user.id_usuario,
            reservas_id_reserva=reserva_id,
            html=html,
        )

    # ---------------------------------------------------------------
    # Correos
    # ---------------------------------------------------------------

    def create_verification_email(
        self,
        user: UserModel,
        verification_link: str
    ):
        self._ensure_valid_user_for_notification(user)

        return self._build_and_send(
            user=user,
            asunto="Verifica tu cuenta Travelers",
            tipo=NOTIFICATION_TYPE_EMAIL_VERIFICATION,
            title="Confirma tu correo",
            preheader="Un clic y tu cuenta queda lista para reservar.",
            eyebrow="Bienvenido a Travelers",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                "Gracias por registrarte en Travelers. Para activar tu cuenta y empezar a reservar, confirma tu correo con el botón.",
            ],
            button=("Verificar mi correo", verification_link),
            note="El enlace vence en 2 horas. Si no creaste esta cuenta, ignora este mensaje.",
        )

    def create_reservation_confirmation_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        payment_hours: int | None = None
    ):
        self._ensure_valid_user_for_notification(user)

        if reservation is None:
            raise ValueError("Reserva inválida")

        if reservation.id_reserva is None:
            raise ValueError("La reserva no tiene id asignado")

        package_name = self._package_name(reservation)

        return self._build_and_send(
            user=user,
            asunto="Confirmación de reserva - Travelers",
            tipo=NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
            reserva_id=reservation.id_reserva,
            title="¡Tu reserva está creada!",
            preheader=f"{package_name} · {long_date(reservation.fecha_reserva)}. Págala para asegurar tu cupo.",
            eyebrow="Reserva pendiente de pago",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                f"Apartamos tu lugar en «{package_name}». Para confirmar la reserva y asegurar el cupo, realiza el pago desde Mis reservas.",
                *(
                    [f"Tienes {payment_hours} {'hora' if payment_hours == 1 else 'horas'} para pagar. "
                     "Te avisaremos antes de que venza; si no se paga a tiempo, la reserva se cancela sola y el cupo queda libre para otros viajeros."]
                    if payment_hours else []
                ),
            ],
            details=[
                ("Código de reserva", reservation.codigo_reserva),
                ("Paquete", package_name),
                ("Fecha del viaje", long_date(reservation.fecha_reserva)),
                ("Viajeros", people_label(reservation.cantidad_personas)),
                ("Valor sin IVA", money(split_iva(reservation.total_reserva)[0])),
                (f"IVA ({IVA_PERCENT} %)", money(split_iva(reservation.total_reserva)[1])),
                ("Total (IVA incluido)", money(reservation.total_reserva)),
            ],
            button=("Pagar mi reserva", f"{frontend_url()}/reservations"),
            note="Los cupos no se guardan hasta que la reserva esté pagada.",
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

        package_name = self._package_name(reservation)

        return self._build_and_send(
            user=user,
            asunto="Confirmación de pago - Travelers",
            tipo=NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
            reserva_id=reservation.id_reserva,
            tone="success",
            title="Pago aprobado: ¡te vas de viaje!",
            preheader=f"Tu reserva {reservation.codigo_reserva} quedó confirmada. Ya puedes descargar tu voucher.",
            eyebrow="Reserva confirmada",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                f"Recibimos tu pago y tu reserva de «{package_name}» quedó confirmada. Descarga tu voucher con código QR y preséntalo el día del viaje.",
            ],
            details=[
                ("Código de reserva", reservation.codigo_reserva),
                ("Fecha del viaje", long_date(reservation.fecha_reserva)),
                ("Método de pago", payment.metodo_pago),
                ("Referencia", payment.referencia_pago),
                ("Valor sin IVA", money(split_iva(payment.valor)[0])),
                (f"IVA ({IVA_PERCENT} %)", money(split_iva(payment.valor)[1])),
                ("Total pagado (IVA incluido)", money(payment.valor)),
            ],
            button=("Descargar mi voucher", f"{frontend_url()}/reservations"),
            note="Lleva tu documento de identidad y el de tus acompañantes.",
        )

    def create_reservation_cancellation_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        by_admin: bool = False,
        expired: bool = False
    ):
        self._ensure_valid_user_for_notification(user)

        if reservation is None or reservation.id_reserva is None:
            raise ValueError("Reserva inválida")

        penalidad = reservation.penalidad_cancelacion or 0
        reembolso = reservation.reembolso or 0

        if expired:
            detalle = (
                "Se venció el plazo para pagarla, así que se canceló automáticamente y su cupo quedó libre. "
                "No se hizo ningún cobro. Si aún quieres viajar, puedes reservar de nuevo mientras haya cupos."
            )
        elif by_admin:
            detalle = "La cancelación la realizó Travelers, así que no tiene penalidad. " + (
                f"Te reembolsaremos el valor completo: {money(reembolso)}."
                if reembolso > 0
                else "La reserva no tenía pagos registrados."
            )
        elif reembolso > 0 and penalidad > 0:
            detalle = (
                f"Como cancelaste después del plazo sin costo, se aplicó una penalidad de {money(penalidad)}. "
                f"Te reembolsaremos {money(reembolso)}."
            )
        elif reembolso > 0:
            detalle = f"Cancelaste dentro del plazo sin costo: te reembolsaremos el valor completo, {money(reembolso)}."
        else:
            detalle = "La reserva no tenía pagos registrados, así que no hay cobros ni reembolsos."

        details = [
            ("Código de reserva", reservation.codigo_reserva),
            ("Paquete", self._package_name(reservation)),
            ("Fecha del viaje", long_date(reservation.fecha_reserva)),
        ]
        if penalidad > 0:
            details.append(("Penalidad", money(penalidad)))
        if reembolso > 0:
            details.append(("Reembolso", money(reembolso)))

        return self._build_and_send(
            user=user,
            asunto="Cancelación de reserva - Travelers",
            tipo=NOTIFICATION_TYPE_RESERVATION_CANCELLATION,
            reserva_id=reservation.id_reserva,
            tone="danger",
            title="Tu reserva fue cancelada",
            preheader=f"Reserva {reservation.codigo_reserva} cancelada.",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                f"Tu reserva {reservation.codigo_reserva} fue cancelada.",
                detalle,
            ],
            details=details,
            button=(
                ("Reservar de nuevo", f"{frontend_url()}/packages/{reservation.id_paquete_turistico}")
                if expired else ("Ver otros paquetes", f"{frontend_url()}/packages")
            ),
            note="Esperamos verte pronto en tu próximo viaje.",
        )

    def create_password_reset_email(
        self,
        user: UserModel,
        reset_link: str
    ):
        self._ensure_valid_user_for_notification(user)

        return self._build_and_send(
            user=user,
            asunto="Recuperación de contraseña - Travelers",
            tipo=NOTIFICATION_TYPE_PASSWORD_RESET,
            title="Restablece tu contraseña",
            preheader="Crea una contraseña nueva para tu cuenta.",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                "Recibimos una solicitud para restablecer la contraseña de tu cuenta. Crea una nueva con el botón.",
            ],
            button=("Crear nueva contraseña", reset_link),
            note="El enlace vence en 30 minutos. Si no lo pediste, ignora este mensaje: tu contraseña no cambiará.",
        )

    def create_payment_reminder_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        hours_left: int
    ):
        self._ensure_valid_user_for_notification(user)

        package_name = self._package_name(reservation)
        cuando = "menos de una hora" if hours_left < 1 else f"{hours_left} {'hora' if hours_left == 1 else 'horas'}"

        return self._build_and_send(
            user=user,
            asunto=f"Tu reserva vence en {cuando} - Travelers",
            tipo=NOTIFICATION_TYPE_PAYMENT_REMINDER,
            reserva_id=reservation.id_reserva,
            tone="warning",
            title="Tu reserva está por vencer",
            preheader=f"Paga tu reserva {reservation.codigo_reserva} para no perder el cupo.",
            eyebrow="Recordatorio de pago",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                f"Tu reserva de «{package_name}» aún no está pagada y el plazo vence en {cuando}.",
                "Si no se paga a tiempo, se cancela sola y el cupo queda libre para otros viajeros.",
            ],
            details=[
                ("Código de reserva", reservation.codigo_reserva),
                ("Paquete", package_name),
                ("Fecha del viaje", long_date(reservation.fecha_reserva)),
                ("Viajeros", people_label(reservation.cantidad_personas)),
                ("Total (IVA incluido)", money(reservation.total_reserva)),
            ],
            button=("Pagar mi reserva", f"{frontend_url()}/reservations"),
            note="Si ya pagaste, ignora este mensaje.",
        )

    def create_trip_reminder_email(
        self,
        user: UserModel,
        reservation: ReservationModel,
        package_name: str,
        days_left: int
    ):
        self._ensure_valid_user_for_notification(user)

        cuando = "mañana" if days_left == 1 else f"en {days_left} días"

        return self._build_and_send(
            user=user,
            asunto=f"Tu viaje es {cuando} - Travelers",
            tipo=NOTIFICATION_TYPE_TRIP_REMINDER,
            reserva_id=reservation.id_reserva,
            title=f"¡Tu viaje es {cuando}!",
            preheader=f"{package_name} · {long_date(reservation.fecha_reserva)}. Ten listo tu voucher.",
            eyebrow="Recordatorio de viaje",
            greeting=f"Hola, {user.nombre}:",
            paragraphs=[
                f"¡Ya casi! Tu viaje «{package_name}» es {cuando}. Descarga tu voucher con código QR para tenerlo a la mano.",
            ],
            details=[
                ("Código de reserva", reservation.codigo_reserva),
                ("Fecha del viaje", long_date(reservation.fecha_reserva)),
                ("Viajeros", people_label(reservation.cantidad_personas)),
            ],
            button=("Ver mi reserva y voucher", f"{frontend_url()}/reservations"),
            note="Lleva tu documento de identidad. ¡Buen viaje!",
        )

    # ---------------------------------------------------------------
    # Consultas
    # ---------------------------------------------------------------

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

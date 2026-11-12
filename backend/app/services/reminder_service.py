import asyncio
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core import clock
from app.core.constants import ADMIN_ROLE_ID, RESERVATION_STATUS_CONFIRMED
from app.models.client_model import ClientModel
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel
from app.services.app_notification_service import AppNotificationService
from app.services.notification_email_service import NotificationEmailService
from app.services.setting_service import SettingService

logger = logging.getLogger(__name__)

CHECK_EVERY_SECONDS = 15 * 60  # cada 15 minutos (los recordatorios nunca se envían dos veces)


class ReminderService:
    """Recordatorios automáticos unos días antes del viaje (correo + campana)."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = SettingService(db)
        self.emails = NotificationEmailService(db)
        self.app_notifications = AppNotificationService(db)

    def due_reservations(self):
        today = clock.today()
        last_day = today + timedelta(days=self.settings.reminder_days())
        return (
            self.db.query(ReservationModel)
            .filter(
                ReservationModel.estado == RESERVATION_STATUS_CONFIRMED,
                ReservationModel.recordatorio_enviado.is_(None),
                ReservationModel.fecha_reserva > today,
                ReservationModel.fecha_reserva <= last_day,
            )
            .all()
        )

    def send_due(self) -> int:
        sent = 0
        today = clock.today()

        for reservation in self.due_reservations():
            client = self.db.query(ClientModel).filter(ClientModel.id_cliente == reservation.cliente_id).first()
            user = (
                self.db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first()
                if client else None
            )
            package = (
                self.db.query(TouristPackageModel)
                .filter(TouristPackageModel.id_paquete_turistico == reservation.id_paquete_turistico)
                .first()
            )
            if user is None or package is None:
                continue

            days_left = (reservation.fecha_reserva - today).days
            self.emails.create_trip_reminder_email(user, reservation, package.nombre, days_left)
            self.app_notifications.notify(
                user.id_usuario,
                "recordatorio_viaje",
                "¡Tu viaje es mañana!" if days_left == 1 else f"Tu viaje es en {days_left} días",
                f"{package.nombre} · {reservation.fecha_reserva:%d/%m/%Y}. Descarga tu voucher.",
                "/reservations",
            )

            reservation.recordatorio_enviado = datetime.now()
            self.db.commit()
            sent += 1

        return sent

    def run_now(self, current_user: UserModel) -> int:
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")
        return self.send_due()


async def reminder_loop(session_factory):
    """
    Tarea de fondo: cada 15 minutos envía los recordatorios de viaje que toquen
    y cancela las reservas pendientes cuyo plazo de pago ya venció.
    """
    from app.services.provider_payment_order_service import ProviderPaymentOrderService  # imports locales: evitan ciclos
    from app.services.reservation_service import ReservationService

    while True:
        try:
            db = session_factory()
            try:
                sent = ReminderService(db).send_due()
                if sent:
                    logger.info("Recordatorios de viaje enviados: %s", sent)
            finally:
                db.close()
        except Exception:
            logger.exception("Falló el envío automático de recordatorios")

        try:
            db = session_factory()
            try:
                reminded = ProviderPaymentOrderService(db).remind_due_approvals()
                if reminded:
                    logger.info("Órdenes de pago por vencer avisadas: %s", reminded)
            finally:
                db.close()
        except Exception:
            logger.exception("Falló el aviso de órdenes de pago por vencer")

        try:
            db = session_factory()
            try:
                reminded = ReservationService(db).remind_unpaid_reservations()
                if reminded:
                    logger.info("Reservas avisadas por plazo de pago: %s", reminded)
            finally:
                db.close()
        except Exception:
            logger.exception("Falló el aviso de reservas por vencer")

        try:
            db = session_factory()
            try:
                expired = ReservationService(db).expire_unpaid_reservations()
                if expired:
                    logger.info("Reservas vencidas por falta de pago: %s", expired)
            finally:
                db.close()
        except Exception:
            logger.exception("Falló la cancelación automática de reservas vencidas")
        await asyncio.sleep(CHECK_EVERY_SECONDS)


def reminders_enabled() -> bool:
    return os.getenv("REMINDERS_ENABLED", "true").lower() == "true"

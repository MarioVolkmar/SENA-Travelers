from sqlalchemy.orm import Session

from app.models.notification_email_model import NotificationEmailModel


class NotificationEmailRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_notification_email(self, notification_email: NotificationEmailModel):
        try:
            self.db.add(notification_email)
            self.db.commit()
            self.db.refresh(notification_email)
            return notification_email

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_notificacion_email: int):
        return (
            self.db.query(NotificationEmailModel)
            .filter(
                NotificationEmailModel.id_notificacion_email
                == id_notificacion_email
            )
            .first()
        )

    def list_notifications(self):
        return self.db.query(NotificationEmailModel).all()

    def list_by_user_id(self, id_usuario: int):
        return (
            self.db.query(NotificationEmailModel)
            .filter(NotificationEmailModel.usuarios_id_usuario == id_usuario)
            .all()
        )

    def list_by_reservation_id(self, reserva_id: int):
        return (
            self.db.query(NotificationEmailModel)
            .filter(NotificationEmailModel.reservas_id_reserva == reserva_id)
            .all()
        )

    def list_by_type(self, tipo_notificacion: str):
        return (
            self.db.query(NotificationEmailModel)
            .filter(
                NotificationEmailModel.tipo_notificacion == tipo_notificacion
            )
            .all()
        )

    def update_status(
        self,
        notification_email: NotificationEmailModel,
        estado_envio: str
    ):
        try:
            notification_email.estado_envio = estado_envio

            self.db.commit()
            self.db.refresh(notification_email)

            return notification_email

        except Exception as error:
            self.db.rollback()
            raise error
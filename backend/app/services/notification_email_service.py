from sqlalchemy.orm import Session

from app.models.notification_email_model import NotificationEmailModel
from app.repositories.notification_email_repository import NotificationEmailRepository
from app.models.user_model import UserModel

from app.core.constants import(
    NOTIFICATION_TYPE_EMAIL_VERIFICATION,
    EMAIL_STATUS_SENT_SIMULATED
)

class NotificationEmailService:
    def __init__(self, db: Session):
        self.notification_email_repository = NotificationEmailRepository(db)

    def create_verification_email(self, user: UserModel, verification_link: str):
        if user is None:
            raise ValueError("Usuario inválido")

        if user.id_usuario is None:
            raise ValueError("El usuario no tiene id asignado")

        if not user.email:
            raise ValueError("El usuario no tiene email")
        
        email = NotificationEmailModel(
            destinatario = user.email,
            asunto = "Verifica tu cuenta Travelers",
            mensaje = f"Hola {user.nombre}, verifica tu cuenta en Travelers usando este enlace: {verification_link}",
            tipo_notificacion = NOTIFICATION_TYPE_EMAIL_VERIFICATION,
            estado_envio=EMAIL_STATUS_SENT_SIMULATED,
            usuarios_id_usuario = user.id_usuario
        )

        return self.notification_email_repository.create_notification_email(email)

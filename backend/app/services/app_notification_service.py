from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLE_ID
from app.models.app_notification_model import AppNotificationModel
from app.models.client_model import ClientModel
from app.models.provider_model import ProviderModel
from app.models.user_model import UserModel

MAX_LISTED = 50


class AppNotificationService:
    """Avisos de la campana: se crean cuando pasa algo que le interesa al usuario."""

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------
    # Crear avisos
    # ---------------------------------------------------------------

    def notify(self, usuario_id: int | None, tipo: str, titulo: str, mensaje: str, enlace: str | None = None):
        if not usuario_id:
            return None
        notification = AppNotificationModel(
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo[:120],
            mensaje=mensaje[:255],
            enlace=enlace,
            leida=False,
        )
        self.db.add(notification)
        self.db.commit()
        return notification

    def notify_admins(self, tipo: str, titulo: str, mensaje: str, enlace: str | None = None):
        admins = self.db.query(UserModel.id_usuario).filter(UserModel.rol_id == ADMIN_ROLE_ID).all()
        for (admin_id,) in admins:
            self.db.add(AppNotificationModel(
                usuario_id=admin_id, tipo=tipo, titulo=titulo[:120], mensaje=mensaje[:255], enlace=enlace, leida=False,
            ))
        self.db.commit()

    def notify_client(self, cliente_id: int, tipo: str, titulo: str, mensaje: str, enlace: str | None = "/reservations"):
        client = self.db.query(ClientModel).filter(ClientModel.id_cliente == cliente_id).first()
        return self.notify(client.usuario_id if client else None, tipo, titulo, mensaje, enlace)

    def notify_provider(self, proveedor_id: int, tipo: str, titulo: str, mensaje: str, enlace: str | None = "/proveedor?seccion=pagos"):
        provider = self.db.query(ProviderModel).filter(ProviderModel.id_proveedor == proveedor_id).first()
        return self.notify(provider.usuario_id if provider else None, tipo, titulo, mensaje, enlace)

    # ---------------------------------------------------------------
    # Consultar y marcar
    # ---------------------------------------------------------------

    def list_mine(self, current_user: UserModel):
        items = (
            self.db.query(AppNotificationModel)
            .filter(AppNotificationModel.usuario_id == current_user.id_usuario)
            .order_by(AppNotificationModel.id_notificacion.desc())
            .limit(MAX_LISTED)
            .all()
        )
        return {"no_leidas": self.unread_count(current_user), "notificaciones": items}

    def unread_count(self, current_user: UserModel) -> int:
        return (
            self.db.query(AppNotificationModel)
            .filter(AppNotificationModel.usuario_id == current_user.id_usuario, AppNotificationModel.leida.is_(False))
            .count()
        )

    def mark_read(self, id_notificacion: int, current_user: UserModel):
        notification = (
            self.db.query(AppNotificationModel)
            .filter(AppNotificationModel.id_notificacion == id_notificacion)
            .first()
        )
        if notification is None:
            raise LookupError("El aviso no existe")
        if notification.usuario_id != current_user.id_usuario:
            raise PermissionError("Este aviso no es tuyo")

        notification.leida = True
        self.db.commit()
        return notification

    def mark_all_read(self, current_user: UserModel):
        (
            self.db.query(AppNotificationModel)
            .filter(AppNotificationModel.usuario_id == current_user.id_usuario, AppNotificationModel.leida.is_(False))
            .update({AppNotificationModel.leida: True}, synchronize_session=False)
        )
        self.db.commit()
        return self.list_mine(current_user)

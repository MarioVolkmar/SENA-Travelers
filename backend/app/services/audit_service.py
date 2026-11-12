import json
from datetime import date, datetime, time

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLE_ID
from app.models.audit_log_model import AuditLogModel
from app.models.user_model import UserModel


class AuditService:
    """Bitácora de acciones de los administradores."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user: UserModel,
        accion: str,
        entidad: str,
        descripcion: str,
        entidad_id: int | None = None,
        cambios: list | None = None,
    ):
        entry = AuditLogModel(
            usuario_id=user.id_usuario,
            usuario_nombre=user.nombre,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            descripcion=descripcion[:255],
            detalle=json.dumps(cambios, ensure_ascii=False) if cambios else None,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def list_entries(
        self,
        current_user: UserModel,
        entidad: str | None = None,
        usuario_id: int | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        buscar: str | None = None,
        limit: int = 500,
    ):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

        query = self.db.query(AuditLogModel)
        if entidad:
            query = query.filter(AuditLogModel.entidad == entidad)
        if usuario_id:
            query = query.filter(AuditLogModel.usuario_id == usuario_id)
        if desde:
            query = query.filter(AuditLogModel.fecha >= datetime.combine(desde, time.min))
        if hasta:
            query = query.filter(AuditLogModel.fecha <= datetime.combine(hasta, time.max))
        if buscar:
            pattern = f"%{buscar}%"
            query = query.filter(or_(AuditLogModel.descripcion.like(pattern), AuditLogModel.detalle.like(pattern)))

        entries = query.order_by(AuditLogModel.id_registro.desc()).limit(min(max(limit, 1), 2000)).all()
        for entry in entries:
            entry.cambios = self.parse_changes(entry.detalle)
        return entries

    @staticmethod
    def parse_changes(detalle: str | None) -> list:
        if not detalle:
            return []
        try:
            changes = json.loads(detalle)
        except ValueError:
            return []
        return changes if isinstance(changes, list) else []

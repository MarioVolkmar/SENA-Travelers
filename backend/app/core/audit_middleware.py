"""
Registra en la bitácora cada cambio exitoso que hace un administrador.

Es un middleware ASGI: mira el método, la ruta y el cuerpo JSON de la petición,
y si la respuesta fue 2xx y el usuario es administrador, guarda una línea legible
("Cambió el rol del usuario #12 a Proveedor").
"""
import json
import logging
import re

from jose import JWTError, jwt

from app.core import security
from app.core.audit_changes import diff, snapshot
from app.core.constants import ADMIN_ROLE_ID

logger = logging.getLogger(__name__)

ROLE_NAMES = {1: "Administrador", 2: "Cliente", 3: "Proveedor"}
MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def _get(body, key, default="?"):
    return body.get(key, default) if isinstance(body, dict) else default


# (método, patrón de ruta, acción, entidad, función que arma la descripción)
RULES = [
    ("POST", r"^/packages/?$", "crear", "paquete", lambda m, b: f"Creó el paquete «{_get(b, 'nombre')}»"),
    ("PATCH", r"^/packages/(\d+)/status$", "cambiar_estado", "paquete",
     lambda m, b: f"Cambió el estado del paquete #{m[1]} a {_get(b, 'estado')}"),
    ("PATCH", r"^/packages/(\d+)$", "editar", "paquete", lambda m, b: f"Editó el paquete #{m[1]}"),
    ("DELETE", r"^/packages/(\d+)$", "eliminar", "paquete", lambda m, b: f"Eliminó el paquete #{m[1]}"),
    ("POST", r"^/packages/(\d+)/images(/upload)?$", "agregar_foto", "paquete",
     lambda m, b: f"Agregó una foto al paquete #{m[1]}"),
    ("PATCH", r"^/packages/(\d+)/images/(\d+)/cover$", "portada", "paquete",
     lambda m, b: f"Cambió la portada del paquete #{m[1]}"),
    ("DELETE", r"^/packages/(\d+)/images/(\d+)$", "quitar_foto", "paquete",
     lambda m, b: f"Quitó la foto #{m[2]} del paquete #{m[1]}"),

    ("POST", r"^/products/?$", "crear", "producto", lambda m, b: f"Creó el producto «{_get(b, 'nombre')}»"),
    ("PATCH", r"^/products/(\d+)/status$", "cambiar_estado", "producto",
     lambda m, b: f"Cambió el estado del producto #{m[1]} a {_get(b, 'estado')}"),
    ("PATCH", r"^/products/(\d+)(/provider)?$", "editar", "producto", lambda m, b: f"Editó el producto #{m[1]}"),
    ("DELETE", r"^/products/(\d+)$", "eliminar", "producto", lambda m, b: f"Eliminó el producto #{m[1]}"),

    ("PATCH", r"^/providers/(\d+)/verification-status$", "verificar", "proveedor",
     lambda m, b: f"Marcó al proveedor #{m[1]} como {_get(b, 'estado_verificacion')}"),
    ("DELETE", r"^/providers/(\d+)$", "eliminar", "proveedor", lambda m, b: f"Eliminó la solicitud de proveedor #{m[1]}"),

    ("PATCH", r"^/users/(\d+)/role$", "cambiar_rol", "usuario",
     lambda m, b: f"Cambió el rol del usuario #{m[1]} a {ROLE_NAMES.get(_get(b, 'rol_id', 0), _get(b, 'rol_id'))}"),
    ("PATCH", r"^/users/(\d+)/activate$", "activar", "usuario", lambda m, b: f"Activó la cuenta del usuario #{m[1]}"),
    ("PATCH", r"^/users/(\d+)/deactivate$", "desactivar", "usuario", lambda m, b: f"Desactivó la cuenta del usuario #{m[1]}"),
    ("PATCH", r"^/users/(\d+)/reset-password$", "restablecer_contrasena", "usuario",
     lambda m, b: f"Restableció la contraseña del usuario #{m[1]}"),
    ("PATCH", r"^/users/(\d+)/(name|email)$", "editar", "usuario", lambda m, b: f"Editó el {m[2] == 'name' and 'nombre' or 'correo'} del usuario #{m[1]}"),
    ("DELETE", r"^/users/(\d+)$", "eliminar", "usuario", lambda m, b: f"Eliminó al usuario #{m[1]}"),

    ("PATCH", r"^/reservations/(\d+)/status$", "cambiar_estado", "reserva",
     lambda m, b: f"Cambió el estado de la reserva #{m[1]} a {_get(b, 'estado')}"),

    ("PATCH", r"^/provider-payments/(\d+)/approve$", "aprobar", "orden_pago", lambda m, b: f"Aprobó la orden de pago #{m[1]}"),
    ("PATCH", r"^/provider-payments/(\d+)/pay$", "pagar", "orden_pago",
     lambda m, b: f"Registró el pago de la orden #{m[1]} (ref. {_get(b, 'referencia_pago')})"),
    ("POST", r"^/provider-payments/(\d+)/receipt$", "adjuntar_comprobante", "orden_pago",
     lambda m, b: f"Adjuntó el comprobante de pago de la orden #{m[1]}"),
    ("PATCH", r"^/provider-payments/(\d+)/annul$", "anular", "orden_pago", lambda m, b: f"Anuló la orden de pago #{m[1]}"),

    ("PATCH", r"^/settings/?$", "configurar", "configuracion",
     lambda m, b: "Cambió la configuración: " + ", ".join(f"{k}={v}" for k, v in (b or {}).items())),
    ("POST", r"^/cities/?$", "crear", "ciudad", lambda m, b: f"Creó la ciudad «{_get(b, 'nombre')}»"),
    ("PATCH", r"^/cities/(\d+)$", "editar", "ciudad", lambda m, b: f"Editó la ciudad #{m[1]}"),

    ("POST", r"^/coupons/?$", "crear", "cupon", lambda m, b: f"Creó el cupón {str(_get(b, 'codigo')).upper()}"),
    ("PATCH", r"^/coupons/(\d+)$", "editar", "cupon", lambda m, b: f"Editó el cupón #{m[1]}"),
    ("DELETE", r"^/coupons/(\d+)$", "eliminar", "cupon", lambda m, b: f"Eliminó el cupón #{m[1]}"),
    ("PATCH", r"^/reviews/(\d+)/status$", "moderar", "resena",
     lambda m, b: f"Marcó la reseña #{m[1]} como {_get(b, 'estado')}"),
    ("POST", r"^/reminders/run$", "enviar", "recordatorio", lambda m, b: "Envió los recordatorios de viaje pendientes"),
]

COMPILED = [(method, re.compile(pattern), action, entity, describe) for method, pattern, action, entity, describe in RULES]


def match_rule(method: str, path: str):
    for rule_method, pattern, action, entity, describe in COMPILED:
        if rule_method != method:
            continue
        found = pattern.match(path)
        if found:
            return action, entity, found, describe
    return None


class AuditMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in MUTATING:
            await self.app(scope, receive, send)
            return

        rule = match_rule(scope["method"], scope["path"].rstrip("/") or "/")
        if rule is None:
            await self.app(scope, receive, send)
            return

        before = self._snapshot_before(scope, rule)
        chunks = []
        status = {"code": 500}

        async def receive_wrapper():
            message = await receive()
            if message["type"] == "http.request":
                chunks.append(message.get("body", b""))
            return message

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        await self.app(scope, receive_wrapper, send_wrapper)

        if 200 <= status["code"] < 300:
            try:
                self._record(scope, rule, b"".join(chunks), before)
            except Exception:  # la bitácora nunca debe romper la petición
                logger.exception("No se pudo registrar la acción en la bitácora")

    @staticmethod
    def _entity_id(found):
        return int(found[1]) if found.lastindex and found[1] and found[1].isdigit() else None

    @staticmethod
    def _session():
        """Generador de sesión de la app (los tests reemplazan get_db por su base de pruebas)."""
        from app.database.connection import get_db
        from app.main import app as fastapi_app

        provider = fastapi_app.dependency_overrides.get(get_db, get_db)
        return provider()

    def _snapshot_before(self, scope, rule):
        """Foto del registro antes del cambio, para luego mostrar qué campos cambiaron."""
        headers = dict(scope.get("headers") or [])
        if not headers.get(b"authorization", b"").decode().lower().startswith("bearer "):
            return None
        _, entity, found, _ = rule
        try:
            generator = self._session()
            db = next(generator)
            try:
                return snapshot(db, entity, self._entity_id(found))
            finally:
                generator.close()
        except Exception:  # la bitácora nunca debe romper la petición
            logger.exception("No se pudo tomar la foto previa para la bitácora")
            return None

    def _record(self, scope, rule, raw_body, before=None):
        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode()
        if not auth.lower().startswith("bearer "):
            return

        try:
            payload = jwt.decode(auth[7:], security.SECRET_KEY, algorithms=[security.ALGORITHM])
        except JWTError:
            return

        content_type = headers.get(b"content-type", b"").decode()
        body = {}
        if raw_body and "application/json" in content_type:
            try:
                body = json.loads(raw_body)
            except ValueError:
                body = {}

        from app.models.user_model import UserModel
        from app.services.audit_service import AuditService

        generator = self._session()
        db = next(generator)
        try:
            user = self._find_user(db, UserModel, payload)
            if user is None or user.rol_id != ADMIN_ROLE_ID:
                return
            action, entity, found, describe = rule
            entity_id = self._entity_id(found)
            after = snapshot(db, entity, entity_id) if before is not None else None
            changes = diff(before, after)

            description = describe(found, body)
            if entity == "configuracion" and changes:
                description = "Cambió la configuración"
            name = (after or before or {}).get("name")
            if name and entity_id is not None and str(name) not in description:
                description = description.replace(f"#{entity_id}", f"#{entity_id} «{name}»", 1)

            AuditService(db).log(user, action, entity, description, entity_id, changes)
        finally:
            generator.close()

    @staticmethod
    def _find_user(db, UserModel, payload):
        subject = payload.get("sub")
        user_id = payload.get("id_usuario") or payload.get("user_id")
        if user_id:
            return db.query(UserModel).filter(UserModel.id_usuario == int(user_id)).first()
        if subject and str(subject).isdigit():
            return db.query(UserModel).filter(UserModel.id_usuario == int(subject)).first()
        if subject:
            return db.query(UserModel).filter(UserModel.email == subject).first()
        return None

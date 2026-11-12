"""
Detalle de los cambios para la bitácora: qué campo cambió y de qué valor a qué valor.

Antes de la petición se toma una "foto" del registro (solo los campos que tienen sentido mostrar),
después se toma otra y se comparan. Nunca se guardan contraseñas, tokens ni datos de inicio de sesión.
"""
from datetime import date, datetime
from decimal import Decimal

from app.core.constants import EDITABLE_SETTINGS_LABELS

ROLE_NAMES = {1: "Administrador", 2: "Cliente", 3: "Proveedor"}
MAX_VALUE_LENGTH = 160


def _city(db, city_id):
    from app.models.city_model import CityModel

    if city_id is None:
        return None
    city = db.query(CityModel).filter(CityModel.id_ciudad == city_id).first()
    return city.nombre if city else f"#{city_id}"


def _provider(db, provider_id):
    from app.models.provider_model import ProviderModel

    if provider_id is None:
        return None
    provider = db.query(ProviderModel).filter(ProviderModel.id_proveedor == provider_id).first()
    return provider.nombre_empresa if provider and provider.nombre_empresa else f"#{provider_id}"


def _money(db, value):
    return None if value is None else f"$ {format_value(Decimal(str(value)))}"


def _includes(value):
    if not isinstance(value, dict):
        return value
    items = [*(value.get("tipos") or []), *(value.get("otros") or [])]
    return ", ".join(str(item).replace("_", " ") for item in items) or None


def _package_products(db, package_id):
    from app.models.product_model import ProductModel
    from app.models.tourist_package_product_model import TouristPackageProductModel

    rows = (
        db.query(ProductModel.nombre, TouristPackageProductModel.cantidad)
        .join(ProductModel, ProductModel.id_producto == TouristPackageProductModel.productos_id_producto)
        .filter(TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico == package_id)
        .all()
    )
    return ", ".join(sorted(f"{name} ×{quantity}" for name, quantity in rows)) or None


def _model_specs():
    """Por cada módulo: modelo, llave, nombre visible y campos (columna → etiqueta o (etiqueta, convertidor))."""
    from app.models.city_model import CityModel
    from app.models.coupon_model import CouponModel
    from app.models.product_model import ProductModel
    from app.models.provider_model import ProviderModel
    from app.models.provider_payment_order_model import ProviderPaymentOrderModel
    from app.models.reservation_model import ReservationModel
    from app.models.review_model import ReviewModel
    from app.models.tourist_package_model import TouristPackageModel
    from app.models.user_model import UserModel

    return {
        "paquete": {
            "model": TouristPackageModel, "key": "id_paquete_turistico", "name": "nombre",
            "fields": {
                "nombre": "Nombre", "descripcion": "Descripción", "precio": ("Precio por persona", _money),
                "descuento": "Descuento (%)", "estado": "Estado", "fecha_inicio": "Fecha de inicio",
                "fecha_fin": "Fecha de fin", "cupo_max": "Cupos",
                "ciudades_id_ciudad": ("Ciudad", _city), "incluye": ("Qué incluye", lambda db, v: _includes(v)),
            },
            "extra": {"Productos incluidos": _package_products},
        },
        "producto": {
            "model": ProductModel, "key": "id_producto", "name": "nombre",
            "fields": {
                "nombre": "Nombre", "descripcion": "Descripción", "tipo_producto": "Tipo",
                "costo": ("Costo", _money), "unidad_cobro": "Unidad de cobro", "estado": "Estado",
                "ciudad_id": ("Ciudad", _city), "proveedor_id": ("Proveedor", _provider),
            },
        },
        "proveedor": {
            "model": ProviderModel, "key": "id_proveedor", "name": "nombre_empresa",
            "fields": {
                "nombre_empresa": "Empresa", "rut": "NIT / RUT", "telefono": "Teléfono", "direccion": "Dirección",
                "estado_verificacion": "Verificación", "ciudad_id": ("Ciudad", _city),
            },
        },
        "usuario": {
            "model": UserModel, "key": "id_usuario", "name": "nombre",
            "fields": {
                "nombre": "Nombre", "email": "Correo", "estado": "Estado de la cuenta",
                "rol_id": ("Rol", lambda db, v: ROLE_NAMES.get(v, v)),
            },
        },
        "reserva": {
            "model": ReservationModel, "key": "id_reserva", "name": "codigo_reserva",
            "fields": {"estado": "Estado", "reembolso": ("Reembolso", _money), "penalidad_cancelacion": ("Penalidad", _money)},
        },
        "orden_pago": {
            "model": ProviderPaymentOrderModel, "key": "id_orden", "name": "codigo",
            "fields": {
                "estado": "Estado", "referencia_pago": "Referencia de pago", "nota": "Nota",
                "comprobante_key": ("Comprobante", lambda db, v: "Adjunto" if v else None),
            },
        },
        "ciudad": {
            "model": CityModel, "key": "id_ciudad", "name": "nombre",
            "fields": {"nombre": "Nombre", "pais": "País", "latitud": "Latitud", "longitud": "Longitud"},
        },
        "cupon": {
            "model": CouponModel, "key": "id_cupon", "name": "codigo",
            "fields": {
                "codigo": "Código", "descripcion": "Descripción", "tipo": "Tipo", "valor": "Valor",
                "fecha_inicio": "Desde", "fecha_fin": "Hasta", "usos_maximos": "Usos máximos",
                "monto_minimo": ("Compra mínima", _money), "estado": "Estado",
            },
        },
        "resena": {
            "model": ReviewModel, "key": "id_resena", "name": None,
            "fields": {"estado": "Estado", "comentario": "Comentario"},
        },
    }


def format_value(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, Decimal):
        value = value.normalize()
        if value == value.to_integral():
            return f"{int(value):,}".replace(",", ".")
        return format(value, "f").replace(".", ",")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) or "—"
    text = " ".join(str(value).split())
    return text if len(text) <= MAX_VALUE_LENGTH else text[: MAX_VALUE_LENGTH - 1] + "…"


def snapshot(db, entity: str, entity_id: int | None):
    """
    Foto legible del registro: {"name": nombre visible, "values": {etiqueta: valor en texto}}.
    None si el módulo no se sigue o el registro no existe.
    """
    if entity == "configuracion":
        from app.services.setting_service import SettingService

        settings = SettingService(db)  # valores vigentes, incluidos los que aún usan el valor por defecto
        return {
            "name": None,
            "values": {label: format_value(settings.get_value(key)) for key, label in EDITABLE_SETTINGS_LABELS.items()},
        }

    spec = _model_specs().get(entity)
    if spec is None or entity_id is None:
        return None

    model = spec["model"]
    row = db.query(model).filter(getattr(model, spec["key"]) == entity_id).first()
    if row is None:
        return None

    values = {}
    for column, label in spec["fields"].items():
        raw = getattr(row, column, None)
        if isinstance(label, tuple):
            label, convert = label
            raw = convert(db, raw)
        values[label] = format_value(raw)
    for label, compute in spec.get("extra", {}).items():
        values[label] = format_value(compute(db, entity_id))

    name = getattr(row, spec["name"], None) if spec["name"] else None
    return {"name": name, "values": values}


def diff(before, after):
    """Lista de cambios [{campo, antes, despues}] entre dos fotos (vacía si no hay cambios)."""
    if not before or not after:
        return []
    changes = []
    for label, old in before["values"].items():
        new = after["values"].get(label, old)
        if old != new:
            changes.append({"campo": label, "antes": old, "despues": new})
    return changes

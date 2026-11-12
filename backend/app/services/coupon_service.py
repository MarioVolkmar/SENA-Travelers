from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import clock
from app.core.constants import (
    ADMIN_ROLE_ID,
    COUPON_STATUS_ACTIVE,
    COUPON_STATUS_INACTIVE,
    COUPON_TYPE_PERCENT,
    COUPON_TYPES,
    COUPON_MIN_PURCHASE_MAX,
    COUPON_PERCENT_MAX,
    COUPON_USES_MAX,
    COUPON_VALUE_MAX,
    COUPON_VALUE_MIN,
)


def pesos(value) -> str:
    return f"${value:,.0f}".replace(",", ".")
from app.models.coupon_model import CouponModel
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel

CENT = Decimal("0.01")


def normalize_code(code: str) -> str:
    return (code or "").strip().upper()


class CouponService:
    """Cupones de descuento: el admin los crea y el viajero los aplica al reservar."""

    def __init__(self, db: Session):
        self.db = db

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_or_raise(self, id_cupon: int):
        coupon = self.db.query(CouponModel).filter(CouponModel.id_cupon == id_cupon).first()
        if coupon is None:
            raise LookupError("El cupón no existe")
        return coupon

    def find_by_code(self, code: str):
        return self.db.query(CouponModel).filter(CouponModel.codigo == normalize_code(code)).first()

    # ---------------------------------------------------------------
    # Reglas
    # ---------------------------------------------------------------

    @staticmethod
    def _validate_fields(data: dict, current=None):
        """
        Valores razonables y fechas coherentes. Al editar (`current`), las fechas solo se
        revisan contra hoy si cambian: un cupón que ya empezó se puede editar sin tocar su inicio.
        """
        tipo = data.get("tipo")
        valor = data.get("valor")
        if tipo is not None and tipo not in COUPON_TYPES:
            raise ValueError("Tipo de cupón no válido")
        if valor is not None and Decimal(valor) <= 0:
            raise ValueError("El valor del descuento debe ser mayor a cero")
        if tipo == COUPON_TYPE_PERCENT and valor is not None and Decimal(valor) > COUPON_PERCENT_MAX:
            raise ValueError(f"El porcentaje debe estar entre 1 y {COUPON_PERCENT_MAX}")
        if tipo != COUPON_TYPE_PERCENT and valor is not None and Decimal(valor) > COUPON_VALUE_MAX:
            raise ValueError(f"El valor del cupón debe ser máximo {pesos(COUPON_VALUE_MAX)}")
        if tipo != COUPON_TYPE_PERCENT and valor is not None and Decimal(valor) < COUPON_VALUE_MIN:
            raise ValueError(f"El valor del cupón debe ser mínimo {pesos(COUPON_VALUE_MIN)}")
        if data.get("usos_maximos") is not None and data["usos_maximos"] > COUPON_USES_MAX:
            raise ValueError(f"Los usos máximos deben ser como mucho {COUPON_USES_MAX:,}".replace(",", "."))
        if data.get("monto_minimo") is not None and Decimal(data["monto_minimo"]) > COUPON_MIN_PURCHASE_MAX:
            raise ValueError(f"La compra mínima debe ser máximo {pesos(COUPON_MIN_PURCHASE_MAX)}")

        inicio, fin = data.get("fecha_inicio"), data.get("fecha_fin")
        if inicio and fin and fin < inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        today = clock.today()
        if inicio and (current is None or inicio != current.fecha_inicio) and inicio < today:
            raise ValueError("La fecha de inicio del cupón no puede ser anterior a hoy")
        if fin and (current is None or fin != current.fecha_fin) and fin < today:
            raise ValueError("La fecha de fin del cupón no puede ser anterior a hoy")

    def discount_for(self, coupon: CouponModel, subtotal: Decimal) -> Decimal:
        """Descuento que da el cupón sobre un total. Lanza ValueError si no aplica."""
        today = clock.today()

        if coupon.estado != COUPON_STATUS_ACTIVE:
            raise ValueError("Este cupón no está activo")
        if today < coupon.fecha_inicio:
            raise ValueError("Este cupón todavía no está vigente")
        if today > coupon.fecha_fin:
            raise ValueError("Este cupón ya venció")
        if coupon.usos_maximos is not None and coupon.usos >= coupon.usos_maximos:
            raise ValueError("Este cupón ya alcanzó su límite de usos")
        if coupon.monto_minimo is not None and subtotal < Decimal(coupon.monto_minimo):
            raise ValueError(f"Este cupón aplica para compras desde ${Decimal(coupon.monto_minimo):,.0f}".replace(",", "."))

        if coupon.tipo == COUPON_TYPE_PERCENT:
            discount = subtotal * Decimal(coupon.valor) / Decimal(100)
        else:
            discount = Decimal(coupon.valor)

        return min(discount, subtotal).quantize(CENT)

    def apply_to_total(self, code: str, subtotal: Decimal):
        """Devuelve (cupón, descuento). Usado al crear la reserva."""
        coupon = self.find_by_code(code)
        if coupon is None:
            raise ValueError("El cupón no existe")
        return coupon, self.discount_for(coupon, subtotal)

    def register_use(self, coupon: CouponModel):
        coupon.usos = (coupon.usos or 0) + 1
        self.db.commit()

    def preview(self, code: str, package_total: Decimal):
        coupon, discount = self.apply_to_total(code, package_total)
        return {
            "codigo": coupon.codigo,
            "descripcion": coupon.descripcion,
            "tipo": coupon.tipo,
            "valor": coupon.valor,
            "subtotal": package_total.quantize(CENT),
            "descuento": discount,
            "total": (package_total - discount).quantize(CENT),
        }

    def validate_for_package(self, code: str, id_paquete: int, personas: int, calculate_total):
        package = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico == id_paquete)
            .first()
        )
        if package is None:
            raise LookupError("El paquete turístico no existe")
        return self.preview(code, Decimal(calculate_total(package, personas)))

    # ---------------------------------------------------------------
    # Administración
    # ---------------------------------------------------------------

    def list_coupons(self, current_user: UserModel):
        self._ensure_admin(current_user)
        return self.db.query(CouponModel).order_by(CouponModel.id_cupon.desc()).all()

    def create(self, data: dict, current_user: UserModel):
        self._ensure_admin(current_user)
        data["codigo"] = normalize_code(data["codigo"])
        self._validate_fields(data)
        if self.find_by_code(data["codigo"]):
            raise ValueError("Ya existe un cupón con ese código")

        coupon = CouponModel(**data, usos=0)
        coupon.estado = data.get("estado") or COUPON_STATUS_ACTIVE
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def update(self, id_cupon: int, data: dict, current_user: UserModel):
        self._ensure_admin(current_user)
        coupon = self._get_or_raise(id_cupon)

        if "codigo" in data:
            data["codigo"] = normalize_code(data["codigo"])
            other = self.find_by_code(data["codigo"])
            if other is not None and other.id_cupon != coupon.id_cupon:
                raise ValueError("Ya existe un cupón con ese código")
        if "estado" in data and data["estado"] not in (COUPON_STATUS_ACTIVE, COUPON_STATUS_INACTIVE):
            raise ValueError("Estado de cupón no válido")

        merged = {
            "tipo": data.get("tipo", coupon.tipo),
            "valor": data.get("valor", coupon.valor),
            "fecha_inicio": data.get("fecha_inicio", coupon.fecha_inicio),
            "fecha_fin": data.get("fecha_fin", coupon.fecha_fin),
            "usos_maximos": data.get("usos_maximos"),
            "monto_minimo": data.get("monto_minimo"),
        }
        self._validate_fields(merged, current=coupon)

        for key, value in data.items():
            setattr(coupon, key, value)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def delete(self, id_cupon: int, current_user: UserModel):
        self._ensure_admin(current_user)
        coupon = self._get_or_raise(id_cupon)
        used = self.db.query(ReservationModel).filter(ReservationModel.cupon_id == coupon.id_cupon).count()
        if used:
            raise ValueError("El cupón ya se usó en reservas: desactívalo en lugar de eliminarlo")
        self.db.delete(coupon)
        self.db.commit()

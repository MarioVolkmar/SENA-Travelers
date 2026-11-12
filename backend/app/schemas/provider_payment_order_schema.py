from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import (
    SETTING_CANCELLATION_FREE_DAYS,
    SETTING_CANCELLATION_PENALTY_PERCENT,
    SETTING_PAYMENT_HOURS,
    SETTING_PROVIDER_PAYMENT_DAY,
    SETTING_PROVIDER_PAYMENT_DAYS,
    SETTING_RANGES,
    SETTING_REMINDER_DAYS,
)


class ProviderPaymentOrderItemResponse(BaseModel):
    producto_id: int
    descripcion: str
    unidad_cobro: str
    cantidad: int
    viajeros: int
    costo_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class ProviderPaymentOrderResponse(BaseModel):
    id_orden: int
    codigo: str
    proveedor_id: int
    nombre_proveedor: str
    reserva_id: int
    codigo_reserva: str
    paquete: str
    fecha_viaje: date
    viajeros: int
    monto: Decimal
    estado: str
    fecha_creacion: Optional[datetime] = None
    fecha_vencimiento: date
    fecha_pago: Optional[datetime] = None
    referencia_pago: Optional[str] = None
    nota: Optional[str] = None
    detalles: List[ProviderPaymentOrderItemResponse] = []
    # Si el proveedor ya registró su cuenta (sin ella no se aprueba ni se paga)
    tiene_datos_bancarios: bool = False
    # Fecha en que se pagará una orden aprobada (día de pago de la configuración)
    fecha_pago_programada: Optional[date] = None
    comprobante_url: Optional[str] = None


class PaymentScheduleResponse(BaseModel):
    dia_pago: int
    proximo_pago: date
    dias_para_aprobar: int


class ProviderPaymentOrderPay(BaseModel):
    referencia_pago: str = Field(..., min_length=3, max_length=60)
    nota: Optional[str] = Field(None, max_length=255)


class ProviderPaymentOrderAnnul(BaseModel):
    nota: str = Field(..., min_length=3, max_length=255)


class GenerateOrdersResponse(BaseModel):
    ordenes_creadas: int


class SettingsResponse(BaseModel):
    dias_pago_proveedores: int
    dias_cancelacion_gratis: int
    porcentaje_penalidad_cancelacion: int
    dias_recordatorio_viaje: int
    horas_para_pagar: int
    dia_pago_proveedores: int


def _setting_field(clave: str):
    minimum, maximum = SETTING_RANGES[clave]
    return Field(None, ge=minimum, le=maximum)


class SettingsUpdate(BaseModel):
    # Los rangos salen de SETTING_RANGES (app/core/constants.py), igual que en el frontend
    dias_pago_proveedores: Optional[int] = _setting_field(SETTING_PROVIDER_PAYMENT_DAYS)
    dias_cancelacion_gratis: Optional[int] = _setting_field(SETTING_CANCELLATION_FREE_DAYS)
    porcentaje_penalidad_cancelacion: Optional[int] = _setting_field(SETTING_CANCELLATION_PENALTY_PERCENT)
    dias_recordatorio_viaje: Optional[int] = _setting_field(SETTING_REMINDER_DAYS)
    horas_para_pagar: Optional[int] = _setting_field(SETTING_PAYMENT_HOURS)
    dia_pago_proveedores: Optional[int] = _setting_field(SETTING_PROVIDER_PAYMENT_DAY)

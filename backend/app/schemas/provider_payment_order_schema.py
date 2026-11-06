from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class SettingsUpdate(BaseModel):
    dias_pago_proveedores: Optional[int] = Field(None, ge=0, le=180)
    dias_cancelacion_gratis: Optional[int] = Field(None, ge=0, le=90)
    porcentaje_penalidad_cancelacion: Optional[int] = Field(None, ge=0, le=100)
    dias_recordatorio_viaje: Optional[int] = Field(None, ge=1, le=30)

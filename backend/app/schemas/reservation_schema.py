from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.companion_schema import CompanionCreate, CompanionResponse


class ReservationCreate(BaseModel):
    id_paquete_turistico: int = Field(..., gt=0)
    fecha_reserva: date
    cantidad_personas: int = Field(..., gt=0)
    acompanantes: List[CompanionCreate] = []
    codigo_cupon: Optional[str] = Field(None, max_length=30)


class ReservationStatusUpdate(BaseModel):
    estado: str = Field(..., min_length=2, max_length=45)


class ReservationResponse(BaseModel):
    id_reserva: int
    fecha_compra: Optional[datetime] = None
    fecha_reserva: date
    cantidad_personas: int
    cliente_id: int
    id_paquete_turistico: int
    total_reserva: Decimal
    estado: str
    codigo_reserva: str
    fecha_cancelacion: Optional[datetime] = None
    penalidad_cancelacion: Optional[Decimal] = None
    reembolso: Optional[Decimal] = None
    cupon_id: Optional[int] = None
    descuento_cupon: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class CancellationPolicyResponse(BaseModel):
    dias_sin_penalidad: int
    porcentaje_penalidad: int


class CancellationPreviewResponse(BaseModel):
    puede_cancelar: bool
    motivo: Optional[str] = None
    fecha_limite_sin_penalidad: date
    con_penalidad: bool
    porcentaje_penalidad: int
    monto_pagado: Decimal
    penalidad: Decimal
    reembolso: Decimal


class PackageAvailabilityResponse(BaseModel):
    id_paquete_turistico: int
    cupo_max: int
    cupos_disponibles: int


class ReservationDetailResponse(ReservationResponse):
    acompanantes: List[CompanionResponse] = []
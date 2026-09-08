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

    model_config = ConfigDict(from_attributes=True)


class ReservationDetailResponse(ReservationResponse):
    acompanantes: List[CompanionResponse] = []
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    reserva_id: int = Field(..., gt=0)
    metodo_pago: str = Field(..., min_length=2, max_length=45)
    valor: Decimal = Field(..., gt=0)


class PaymentResponse(BaseModel):
    id_pago: int
    metodo_pago: str
    valor: Decimal
    estado_pago: str
    fecha_pago: Optional[datetime] = None
    referencia_pago: str
    reserva_id: int

    model_config = ConfigDict(from_attributes=True)
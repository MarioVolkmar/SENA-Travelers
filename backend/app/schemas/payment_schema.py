from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.constants import IVA_PERCENT
from app.core.taxes import split_iva


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

    # Desglose del IVA del valor pagado (el valor ya lo incluye)
    @computed_field
    @property
    def valor_sin_iva(self) -> Decimal:
        return split_iva(self.valor)[0]

    @computed_field
    @property
    def iva(self) -> Decimal:
        return split_iva(self.valor)[1]

    @computed_field
    @property
    def iva_porcentaje(self) -> int:
        return IVA_PERCENT
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CompanionCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    documento: str = Field(..., min_length=5, max_length=45)
    fecha_nacimiento: date


class CompanionResponse(CompanionCreate):
    id_acompanante: int
    reserva_id: int

    model_config = ConfigDict(from_attributes=True)
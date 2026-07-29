from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProviderBase(BaseModel):
    rut: str = Field(..., min_length=5, max_length=30)
    telefono: str = Field(..., min_length=7, max_length=30)
    direccion: str = Field(..., min_length=5, max_length=45)
    nombre_empresa: str = Field(..., min_length=2, max_length=100)
    ciudad_id: int = Field(..., gt=0)


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    telefono: Optional[str] = Field(None, min_length=7, max_length=30)
    direccion: Optional[str] = Field(None, min_length=5, max_length=45)
    nombre_empresa: Optional[str] = Field(None, min_length=2, max_length=100)
    ciudad_id: Optional[int] = Field(None, gt=0)


class ProviderVerificationUpdate(BaseModel):
    estado_verificacion: str = Field(..., min_length=2, max_length=45)


class ProviderResponse(ProviderBase):
    id_proveedor: int
    usuario_id: int
    estado_verificacion: str
    fecha_solicitud: Optional[datetime] = None
    fecha_verificacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
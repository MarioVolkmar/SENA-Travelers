from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TouristPackageProductCreate(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(default=1, gt=0)


class TouristPackageProductResponse(BaseModel):
    producto_id: int
    cantidad: int


class TouristPackageBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: str = Field(..., min_length=10)
    precio: Decimal = Field(..., gt=0)
    descuento: int = Field(default=0, ge=0)
    fecha_inicio: date
    fecha_fin: date
    cupo_max: int = Field(..., gt=0)
    ciudad_id: int = Field(..., gt=0)


class TouristPackageCreate(TouristPackageBase):
    productos: List[TouristPackageProductCreate] = Field(..., min_length=1)


class TouristPackageUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, min_length=10)
    precio: Optional[Decimal] = Field(None, gt=0)
    descuento: Optional[int] = Field(None, ge=0)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cupo_max: Optional[int] = Field(None, gt=0)
    ciudad_id: Optional[int] = Field(None, gt=0)


class TouristPackageStatusUpdate(BaseModel):
    estado: str = Field(..., min_length=2, max_length=35)


class TouristPackageResponse(TouristPackageBase):
    id_paquete_turistico: int
    estado: str

    model_config = ConfigDict(from_attributes=True)


class TouristPackageDetailResponse(TouristPackageResponse):
    productos: List[TouristPackageProductResponse] = []
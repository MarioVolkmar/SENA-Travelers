from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: str = Field(..., min_length=10)
    tipo_producto: str = Field(..., min_length=2, max_length=45)
    costo: Decimal = Field(..., gt=0)
    ciudad_id: int = Field(..., gt=0)
    proveedor_id: int = Field(..., gt=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, min_length=10)
    tipo_producto: Optional[str] = Field(None, min_length=2, max_length=45)
    costo: Optional[Decimal] = Field(None, gt=0)
    ciudad_id: Optional[int] = Field(None, gt=0)


class ProductStatusUpdate(BaseModel):
    estado: str = Field(..., min_length=2, max_length=45)


class ProductProviderUpdate(BaseModel):
    proveedor_id: int = Field(..., gt=0)


class ProductResponse(ProductBase):
    id_producto: int
    estado: str

    model_config = ConfigDict(from_attributes=True)
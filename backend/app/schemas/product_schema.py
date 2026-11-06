from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.core.constants import PRODUCT_TYPES, PRODUCT_UNITS


def validate_product_type(value):
    if value is None:
        return value

    value = value.strip().lower()

    if value not in PRODUCT_TYPES:
        raise ValueError("Tipo de producto no válido. Opciones: " + ", ".join(PRODUCT_TYPES))

    return value


def validate_product_unit(value):
    if value is None:
        return value

    value = value.strip().lower()

    if value not in PRODUCT_UNITS:
        raise ValueError("Unidad de cobro no válida. Opciones: " + ", ".join(PRODUCT_UNITS))

    return value


class ProductBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: str = Field(..., min_length=10)
    tipo_producto: str = Field(..., min_length=2, max_length=45)
    costo: Decimal = Field(..., gt=0)
    ciudad_id: int = Field(..., gt=0)
    proveedor_id: int = Field(..., gt=0)
    unidad_cobro: str = Field(default="persona", max_length=20)


class ProductCreate(ProductBase):
    @field_validator("tipo_producto")
    @classmethod
    def check_product_type(cls, value):
        return validate_product_type(value)

    @field_validator("unidad_cobro")
    @classmethod
    def check_unit(cls, value):
        return validate_product_unit(value)


class ProductUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, min_length=10)
    tipo_producto: Optional[str] = Field(None, min_length=2, max_length=45)
    costo: Optional[Decimal] = Field(None, gt=0)
    ciudad_id: Optional[int] = Field(None, gt=0)
    unidad_cobro: Optional[str] = Field(None, max_length=20)

    @field_validator("tipo_producto")
    @classmethod
    def check_product_type(cls, value):
        return validate_product_type(value)

    @field_validator("unidad_cobro")
    @classmethod
    def check_unit(cls, value):
        return validate_product_unit(value)


class ProductStatusUpdate(BaseModel):
    estado: str = Field(..., min_length=2, max_length=45)


class ProductProviderUpdate(BaseModel):
    proveedor_id: int = Field(..., gt=0)


class ProductResponse(ProductBase):
    id_producto: int
    estado: str

    model_config = ConfigDict(from_attributes=True)


class ProductTypeResponse(BaseModel):
    clave: str
    nombre: str
    ejemplos: str


class ProductUnitResponse(BaseModel):
    clave: str
    nombre: str

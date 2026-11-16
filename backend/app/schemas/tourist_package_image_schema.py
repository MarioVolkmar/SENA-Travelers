from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TouristPackageImageBase(BaseModel):
    s3_key: str = Field(..., min_length=1, max_length=500)
    es_portada: bool = False
    orden: int = Field(default=0, ge=0)


class TouristPackageImageCreate(TouristPackageImageBase):
    pass


class TouristPackageImageResponse(TouristPackageImageBase):
    id_imagen: int
    paquete_id: int
    imagen_url: Optional[str] = None
    # Versión pequeña para tarjetas y miniaturas (si no existe, es la misma imagen_url)
    imagen_url_sm: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

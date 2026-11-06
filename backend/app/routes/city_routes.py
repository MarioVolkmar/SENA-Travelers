from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLE_ID
from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.city_model import CityModel
from app.models.user_model import UserModel
from app.repositories.city_repository import CityRepository
from app.services.geocoding_service import find_coordinates


class CityCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=45)
    departamento: str = Field(..., min_length=2, max_length=45)
    pais: str = Field(default="Colombia", min_length=2, max_length=45)
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180)


class CityUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=45)
    departamento: Optional[str] = Field(None, min_length=2, max_length=45)
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180)
    # Vuelve a buscar la ubicación con el nombre y el departamento
    recalcular_ubicacion: bool = False


class CityResponse(BaseModel):
    id_ciudad: int
    nombre: str
    departamento: str
    pais: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(
    prefix="/cities",
    tags=["Cities"]
)


@router.get("/", response_model=List[CityResponse])
def list_cities(db: Session = Depends(get_db)):
    """Lista pública de ciudades (para formularios del frontend)."""
    return CityRepository(db).list_cities()


@router.post("/", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(
    city_data: CityCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Agrega un destino nuevo. Solo administradores."""
    if current_user.rol_id != ADMIN_ROLE_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    nombre = city_data.nombre.strip()
    departamento = city_data.departamento.strip()

    duplicated = (
        db.query(CityModel)
        .filter(
            func.lower(CityModel.nombre) == nombre.lower(),
            func.lower(CityModel.departamento) == departamento.lower()
        )
        .first()
    )

    if duplicated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esa ciudad ya está registrada"
        )

    latitud, longitud = city_data.latitud, city_data.longitud
    pais = city_data.pais.strip()

    # Si no se enviaron coordenadas, el servidor las busca solo
    if latitud is None or longitud is None:
        found = find_coordinates(nombre, departamento, pais)
        latitud, longitud = found if found else (None, None)

    return CityRepository(db).create_city(
        CityModel(
            nombre=nombre,
            departamento=departamento,
            pais=pais,
            latitud=latitud,
            longitud=longitud,
        )
    )


@router.patch("/{id_ciudad}", response_model=CityResponse)
def update_city(
    id_ciudad: int,
    city_data: CityUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Edita un destino (por ejemplo, su ubicación en el mapa). Solo administradores."""
    if current_user.rol_id != ADMIN_ROLE_ID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para realizar esta acción")

    city = db.query(CityModel).filter(CityModel.id_ciudad == id_ciudad).first()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La ciudad no existe")

    changes = city_data.model_dump(exclude_unset=True)
    recalculate = changes.pop("recalcular_ubicacion", False)

    for key, value in changes.items():
        setattr(city, key, value.strip() if isinstance(value, str) else value)

    if recalculate:
        found = find_coordinates(city.nombre, city.departamento, city.pais)
        if found is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontró la ubicación de esa ciudad. Escribe las coordenadas a mano.",
            )
        city.latitud, city.longitud = found

    db.commit()
    db.refresh(city)
    return city

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    rol_id: int = Field(..., gt=0)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    estado: Optional[str] = None
    verificacion_email: Optional[str] = None
    rol_id: Optional[int] = Field(None, gt=0)


class UserResponse(UserBase):
    id_usuario: int
    estado: str
    verificacion_email: str
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
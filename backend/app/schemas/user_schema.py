from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    rol_id: int = Field(..., gt=0)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserResponse(UserBase):
    id_usuario: int
    estado: str
    verificacion_email: str
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserNameUpdate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
class UserEmailUpdate(BaseModel):
    email: EmailStr
class UserPasswordUpdate(BaseModel):
    actual_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)
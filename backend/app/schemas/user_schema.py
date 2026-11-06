from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.core.storage import photo_public_url


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class ProviderRegistration(BaseModel):
    """Datos de la empresa cuando la cuenta se registra como proveedor."""
    rut: str = Field(..., min_length=5, max_length=30)
    telefono: str = Field(..., min_length=7, max_length=30)
    direccion: str = Field(..., min_length=5, max_length=45)
    nombre_empresa: str = Field(..., min_length=2, max_length=100)
    ciudad_id: int = Field(..., gt=0)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    # Si viene, además de la cuenta se crea la solicitud de proveedor (pendiente de aprobación)
    proveedor: Optional[ProviderRegistration] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserResponse(UserBase):
    id_usuario: int
    estado: str
    rol_id: int
    verificacion_email: str
    fecha_creacion: Optional[datetime] = None
    google_conectado: bool = False
    tiene_contrasena: bool = True
    foto_url: Optional[str] = None

    @field_validator("foto_url")
    @classmethod
    def build_photo_url(cls, value):
        # En la base se guarda la clave de S3 ("avatars/...") o la URL de Google
        return photo_public_url(value)

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserNameUpdate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
class UserEmailUpdate(BaseModel):
    email: EmailStr
class UserPasswordUpdate(BaseModel):
    # Opcional solo para cuentas de Google que todavía no tienen contraseña
    actual_password: Optional[str] = Field(None, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)
class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100)
class UserRoleUpdate(BaseModel):
    rol_id: int = Field(..., gt=0)

class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., min_length=20)

class GoogleConfigResponse(BaseModel):
    enabled: bool
    client_id: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.product_schema import ProductResponse


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

    # Cuenta donde recibe los pagos de la agencia
    banco: Optional[str] = Field(None, min_length=2, max_length=60)
    tipo_cuenta: Optional[Literal["ahorros", "corriente"]] = None
    numero_cuenta: Optional[str] = Field(None, min_length=5, max_length=30, pattern=r"^[0-9-]+$")
    titular_cuenta: Optional[str] = Field(None, min_length=2, max_length=100)


class ProviderVerificationUpdate(BaseModel):
    estado_verificacion: str = Field(..., min_length=2, max_length=45)


class ProviderPackageItem(BaseModel):
    id_paquete_turistico: int
    nombre: str
    ciudad_id: int
    fecha_inicio: date
    fecha_fin: date
    estado: str
    productos: List[str]
    viajeros_confirmados: int
    reservas_confirmadas: int
    viajeros_pendientes: int


class ProviderDashboardSummary(BaseModel):
    productos_activos: int
    paquetes: int
    viajeros_proximos: int


class ProviderResponse(ProviderBase):
    id_proveedor: int
    usuario_id: int
    estado_verificacion: str
    fecha_solicitud: Optional[datetime] = None
    fecha_verificacion: Optional[datetime] = None
    banco: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    numero_cuenta: Optional[str] = None
    titular_cuenta: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProviderDashboardResponse(BaseModel):
    proveedor: ProviderResponse
    productos: List[ProductResponse]
    paquetes: List[ProviderPackageItem]
    resumen: ProviderDashboardSummary

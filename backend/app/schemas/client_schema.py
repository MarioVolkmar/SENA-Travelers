from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ClientBase(BaseModel):
    usuario_id: int = Field(..., gt = 0)
    identificacion: str = Field(..., min_length= 1, max_length= 45)
    fecha_nacimiento: date
    ciudad_id: int = Field(..., gt = 0)


class ClientUpdate(BaseModel):
    ciudad_id: Optional[int] = Field(None,  gt=0)


class ClientResponse(ClientBase):
    usuario_id: int 
    identificacion: str 
    fecha_nacimiento: date
    ciudad_id: int 

    model_config = ConfigDict(from_attributes=True)
from datetime import date

from pydantic import BaseModel , Field, ConfigDict


class ClientBase(BaseModel):
    identificacion: str = Field(..., min_length= 5, max_length= 30)
    fecha_nacimiento: date
    ciudad_id: int = Field(..., gt = 0)

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    ciudad_id: int = Field(...,  gt=0)


class ClientResponse(ClientBase):
    usuario_id: int 
    id_cliente: int

    model_config = ConfigDict(from_attributes=True)
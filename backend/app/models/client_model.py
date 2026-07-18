from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.role_model import RoleModel


class ClientModel(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usario"), nullable=False)
    identificacion = Column(String(45), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False, server_default=func.current_date())
    ciudad_id = Column(Integer, ForeignKey("ciudades.id_ciudad"), nullable=False)
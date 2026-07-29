from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.user_model import UserModel
from app.models.city_model import CityModel


class ProviderModel(Base):
    __tablename__ = "proveedores"

    id_proveedor = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False, unique=True)
    rut = Column(String(30), nullable=False, unique=True)
    telefono = Column(String(30), nullable=False)
    direccion = Column(String(45), nullable=False)
    nombre_empresa = Column(String(100), nullable=False)
    fecha_verificacion = Column(DateTime, nullable=True)
    fecha_solicitud = Column(DateTime, nullable=False, server_default=func.now())
    estado_verificacion = Column(String(45), nullable=False, default="pendiente")
    ciudad_id = Column(Integer, ForeignKey("ciudades.id_ciudad"), nullable=False)
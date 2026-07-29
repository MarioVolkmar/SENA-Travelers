from sqlalchemy import Column, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from app.database.base import Base
from app.models.city_model import CityModel
from app.models.provider_model import ProviderModel


class ProductModel(Base):
    __tablename__ = "productos"

    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ciudad_id = Column(Integer, ForeignKey("ciudades.id_ciudad"), nullable=False)
    descripcion = Column(MEDIUMTEXT, nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id_proveedor"), nullable=False)
    nombre = Column(String(100), nullable=False)
    tipo_producto = Column(String(45), nullable=False)
    estado = Column(String(45), nullable=False, default="activo")
    costo = Column(DECIMAL(10, 2), nullable=False)
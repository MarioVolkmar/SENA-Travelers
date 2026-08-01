from sqlalchemy import Column, ForeignKey, Integer

from app.database.base import Base
from app.models.tourist_package_model import TouristPackageModel
from app.models.product_model import ProductModel


class TouristPackageProductModel(Base):
    __tablename__ = "paquetes_turisticos_has_productos"

    paquetes_turisticos_id_paquete_turistico = Column(Integer, ForeignKey("paquetes_turisticos.id_paquete_turistico"), primary_key=True, nullable=False)
    productos_id_producto = Column(Integer, ForeignKey("productos.id_producto"), primary_key=True, nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
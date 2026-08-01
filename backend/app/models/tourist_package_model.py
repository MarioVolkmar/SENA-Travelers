from sqlalchemy import Column, Date, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from app.database.base import Base
from app.models.city_model import CityModel


class TouristPackageModel(Base):
    __tablename__ = "paquetes_turisticos"

    id_paquete_turistico = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(MEDIUMTEXT, nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False)
    descuento = Column(Integer, nullable=False, default=0)
    estado = Column(String(35), nullable=False, default="activo")
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    cupo_max = Column(Integer, nullable=False)
    ciudades_id_ciudad = Column(Integer, ForeignKey("ciudades.id_ciudad"), nullable=False)

    @property
    def ciudad_id(self):
        return self.ciudades_id_ciudad
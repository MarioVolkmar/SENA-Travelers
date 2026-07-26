from sqlalchemy import Column, Integer, String

from app.database.base import Base

class CityModel(Base):
    __tablename__ = "ciudades"

    id_ciudad = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(45), nullable=False)
    departamento =  Column(String(45), nullable=False)
    pais = Column(String(45), nullable=False)
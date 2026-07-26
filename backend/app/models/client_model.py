from sqlalchemy import Column, Date, ForeignKey, Integer, String


from app.database.base import Base
from app.models.user_model import UserModel
from app.models.city_model import CityModel


class ClientModel(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False, unique=True)
    identificacion = Column(String(30), nullable=False, unique=True)
    fecha_nacimiento = Column(Date, nullable=False)
    ciudad_id = Column(Integer, ForeignKey("ciudades.id_ciudad"), nullable=False)
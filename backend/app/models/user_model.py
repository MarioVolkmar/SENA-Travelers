from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.role_model import RoleModel


class UserModel(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    estado = Column(String(45), nullable=False, default="activo")
    fecha_creacion = Column(DateTime, nullable=False, server_default=func.now())
    verificacion_email = Column(String(45), nullable=False, default="pendiente")
    rol_id = Column(Integer, ForeignKey("roles.id_rol"), nullable=False,  default= 2)
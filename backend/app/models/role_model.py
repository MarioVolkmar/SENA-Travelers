from sqlalchemy import Column, Integer, String

from app.database.base import Base


class RoleModel(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, index=True, autoincrement=True)
    descripcion = Column(String(45), nullable=False, unique=True)
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text
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

    # Identificador de la cuenta de Google vinculada (claim "sub" del token)
    google_sub = Column(String(255), nullable=True, unique=True)

    # False en las cuentas creadas con Google hasta que el usuario crea una contraseña
    tiene_contrasena = Column(Boolean, nullable=False, default=True, server_default=text("1"))

    # Foto de perfil: clave de S3 ("avatars/...") si la subió, o la URL de su foto de Google
    foto_url = Column(String(500), nullable=True)

    @property
    def google_conectado(self):
        return self.google_sub is not None

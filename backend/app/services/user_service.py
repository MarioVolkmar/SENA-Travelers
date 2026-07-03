from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user_model import UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def hash_password(self, password: str):
        return password_context.hash(password)

    def create_user(self, user_data: UserCreate):
        existing_user = self.user_repository.find_by_email(user_data.email)

        if existing_user is not None:
            raise ValueError("El email ya está registrado")

        contrasena_hash = self.hash_password(user_data.password)

        user = UserModel(
            nombre=user_data.nombre,
            email=user_data.email,
            contrasena_hash=contrasena_hash,
            rol_id=user_data.rol_id
        )

        return self.user_repository.create_user(user)

    def get_user_by_id(self, id_usuario: int):
        user = self.user_repository.find_by_id(id_usuario)

        if user is None:
            raise ValueError("El usuario no existe")

        return user

    def list_users(self):
        return self.user_repository.list_users()

    def deactivate_user(self, id_usuario: int):
        user = self.user_repository.deactivate_user(id_usuario)

        if user is None:
            raise ValueError("El usuario no existe")

        return user
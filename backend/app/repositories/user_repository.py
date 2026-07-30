from sqlalchemy.orm import Session

from app.models.user_model import UserModel
from app.core.constants import (
    USER_STATUS_ACTIVE,
    USER_STATUS_INACTIVE
)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserModel):
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_email(self, email: str):
        return (
            self.db.query(UserModel)
            .filter(UserModel.email == email)
            .first()
        )

    def find_by_id(self, id_usuario: int):
        return (
            self.db.query(UserModel)
            .filter(UserModel.id_usuario == id_usuario)
            .first()
        )

    def update_email(self, user: UserModel, email: str):
        try:
            user.email = email

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def update_password(self, user: UserModel, contrasena_hash: str):
        try:
            user.contrasena_hash = contrasena_hash

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def update_name(self, user: UserModel, name: str):
        try:
            user.nombre = name

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def update_verification_email(self, user: UserModel, verification_email: str):
        try:
            user.verificacion_email = verification_email

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def deactivate_user(self, user: UserModel):
        try:
            user.estado = USER_STATUS_INACTIVE

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def activate_user(self, user: UserModel):
        try:
            user.estado = USER_STATUS_ACTIVE

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def update_user_role(self, user: UserModel, rol_id: int):
        try:
            user.rol_id = rol_id

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def list_users(self):
        return self.db.query(UserModel).all()
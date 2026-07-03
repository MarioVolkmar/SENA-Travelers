from sqlalchemy.orm import Session

from app.models.user_model import UserModel


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

    def deactivate_user(self, id_usuario: int):
        try:
            user = self.find_by_id(id_usuario)

            if user is None:
                return None

            user.estado = "inactivo"

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception as error:
            self.db.rollback()
            raise error

    def list_users(self):
        return self.db.query(UserModel).all()
from sqlalchemy.orm import Session

from app.models.role_model import RoleModel

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_role_by_id(self, id_rol: int):
        return (
            self.db.query(RoleModel)
            .filter(RoleModel.id_rol == id_rol)
            .first()
        )
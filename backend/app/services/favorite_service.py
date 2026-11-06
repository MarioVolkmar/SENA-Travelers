from sqlalchemy.orm import Session

from app.models.favorite_model import FavoriteModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel


class FavoriteService:
    """Lista de paquetes guardados por cada usuario."""

    def __init__(self, db: Session):
        self.db = db

    def _get_package_or_raise(self, paquete_id: int):
        package = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico == paquete_id)
            .first()
        )
        if package is None:
            raise LookupError("El paquete turístico no existe")
        return package

    def list_ids(self, current_user: UserModel):
        rows = (
            self.db.query(FavoriteModel.paquete_id)
            .filter(FavoriteModel.usuario_id == current_user.id_usuario)
            .all()
        )
        return [paquete_id for (paquete_id,) in rows]

    def list_packages(self, current_user: UserModel):
        return (
            self.db.query(TouristPackageModel)
            .join(FavoriteModel, FavoriteModel.paquete_id == TouristPackageModel.id_paquete_turistico)
            .filter(FavoriteModel.usuario_id == current_user.id_usuario)
            .order_by(FavoriteModel.id_favorito.desc())
            .all()
        )

    def add(self, paquete_id: int, current_user: UserModel):
        self._get_package_or_raise(paquete_id)

        existing = (
            self.db.query(FavoriteModel)
            .filter(FavoriteModel.usuario_id == current_user.id_usuario, FavoriteModel.paquete_id == paquete_id)
            .first()
        )
        if existing is None:
            self.db.add(FavoriteModel(usuario_id=current_user.id_usuario, paquete_id=paquete_id))
            self.db.commit()

        return self.list_ids(current_user)

    def remove(self, paquete_id: int, current_user: UserModel):
        (
            self.db.query(FavoriteModel)
            .filter(FavoriteModel.usuario_id == current_user.id_usuario, FavoriteModel.paquete_id == paquete_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return self.list_ids(current_user)

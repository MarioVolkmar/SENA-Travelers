from sqlalchemy.orm import Session

from app.models.tourist_package_image_model import TouristPackageImageModel


class TouristPackageImageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_image(self, image: TouristPackageImageModel):
        try:
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)

            return image

        except Exception:
            self.db.rollback()
            raise

    def find_by_id(self, id_imagen: int):
        return (
            self.db.query(TouristPackageImageModel)
            .filter(TouristPackageImageModel.id_imagen == id_imagen)
            .first()
        )

    def find_by_s3_key(self, paquete_id: int, s3_key: str):
        return (
            self.db.query(TouristPackageImageModel)
            .filter(
                TouristPackageImageModel.paquete_id == paquete_id,
                TouristPackageImageModel.s3_key == s3_key
            )
            .first()
        )

    def list_by_package_id(self, paquete_id: int):
        return (
            self.db.query(TouristPackageImageModel)
            .filter(TouristPackageImageModel.paquete_id == paquete_id)
            .order_by(
                TouristPackageImageModel.es_portada.desc(),
                TouristPackageImageModel.orden.asc()
            )
            .all()
        )

    def find_cover_by_package_id(self, paquete_id: int):
        return (
            self.db.query(TouristPackageImageModel)
            .filter(
                TouristPackageImageModel.paquete_id == paquete_id,
                TouristPackageImageModel.es_portada.is_(True)
            )
            .first()
        )

    def list_covers(self):
        return (
            self.db.query(TouristPackageImageModel)
            .filter(TouristPackageImageModel.es_portada.is_(True))
            .all()
        )

    def set_cover(self, image: TouristPackageImageModel):
        """Marca la imagen como portada y desmarca la portada anterior."""
        try:
            (
                self.db.query(TouristPackageImageModel)
                .filter(
                    TouristPackageImageModel.paquete_id == image.paquete_id,
                    TouristPackageImageModel.id_imagen != image.id_imagen
                )
                .update(
                    {TouristPackageImageModel.es_portada: False},
                    synchronize_session=False
                )
            )

            image.es_portada = True

            self.db.commit()
            self.db.refresh(image)

            return image

        except Exception:
            self.db.rollback()
            raise

    def delete_image(self, image: TouristPackageImageModel):
        try:
            self.db.delete(image)
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

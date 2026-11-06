from sqlalchemy.orm import Session

from app.models.tourist_package_model import TouristPackageModel
from app.models.tourist_package_product_model import TouristPackageProductModel
from app.core.constants import TOURIST_PACKAGE_STATUS_ACTIVE


class TouristPackageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_package(self, tourist_package: TouristPackageModel):
        try:
            self.db.add(tourist_package)
            self.db.commit()
            self.db.refresh(tourist_package)
            return tourist_package
        except Exception as error:
            self.db.rollback()
            raise error

    def add_product_to_package(
        self,
        package_id: int,
        product_id: int,
        cantidad: int
    ):
        try:
            package_product = TouristPackageProductModel(
                paquetes_turisticos_id_paquete_turistico=package_id,
                productos_id_producto=product_id,
                cantidad=cantidad
            )

            self.db.add(package_product)
            self.db.commit()
            self.db.refresh(package_product)

            return package_product

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_paquete_turistico: int):
        return (
            self.db.query(TouristPackageModel)
            .filter(
                TouristPackageModel.id_paquete_turistico
                == id_paquete_turistico
            )
            .first()
        )

    def list_packages(self):
        return self.db.query(TouristPackageModel).all()

    def list_active_packages(self, ends_after=None):
        """Paquetes activos; con ends_after solo los que terminan después de esa fecha."""
        query = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.estado == TOURIST_PACKAGE_STATUS_ACTIVE)
        )

        if ends_after is not None:
            query = query.filter(TouristPackageModel.fecha_fin > ends_after)

        return query.order_by(TouristPackageModel.fecha_inicio.asc()).all()

    def list_by_city_id(self, ciudad_id: int):
        return (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.ciudades_id_ciudad == ciudad_id)
            .all()
        )

    def list_active_by_city_id(self, ciudad_id: int, ends_after=None):
        query = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.ciudades_id_ciudad == ciudad_id)
            .filter(TouristPackageModel.estado == TOURIST_PACKAGE_STATUS_ACTIVE)
        )

        if ends_after is not None:
            query = query.filter(TouristPackageModel.fecha_fin > ends_after)

        return query.order_by(TouristPackageModel.fecha_inicio.asc()).all()

    def list_package_products(self, package_id: int):
        return (
            self.db.query(TouristPackageProductModel)
            .filter(
                TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico
                == package_id
            )
            .all()
        )

    def update_package(self, tourist_package: TouristPackageModel, package_data: dict):
        try:
            for field, value in package_data.items():
                if value is not None:
                    setattr(tourist_package, field, value)

            self.db.commit()
            self.db.refresh(tourist_package)

            return tourist_package

        except Exception as error:
            self.db.rollback()
            raise error

    def update_status(self, tourist_package: TouristPackageModel, estado: str):
        try:
            tourist_package.estado = estado

            self.db.commit()
            self.db.refresh(tourist_package)

            return tourist_package

        except Exception as error:
            self.db.rollback()
            raise error

    def delete_package_products(self, package_id: int):
        try:
            (
                self.db.query(TouristPackageProductModel)
                .filter(
                    TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico
                    == package_id
                )
                .delete()
            )

            self.db.commit()

        except Exception as error:
            self.db.rollback()
            raise error
from sqlalchemy.orm import Session

from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel

from app.repositories.tourist_package_repository import TouristPackageRepository
from app.repositories.city_repository import CityRepository
from app.repositories.product_repository import ProductRepository

from app.schemas.tourist_package_schema import (
    TouristPackageCreate,
    TouristPackageUpdate,
    TouristPackageStatusUpdate,
)

from app.core.constants import (
    ADMIN_ROLE_ID,
    PRODUCT_STATUS_ACTIVE,
    TOURIST_PACKAGE_STATUS_ACTIVE,
    ALLOWED_TOURIST_PACKAGE_STATUS,
)


class TouristPackageService:
    def __init__(self, db: Session):
        self.tourist_package_repository = TouristPackageRepository(db)
        self.city_repository = CityRepository(db)
        self.product_repository = ProductRepository(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_package_or_raise(self, id_paquete_turistico: int):
        tourist_package = self.tourist_package_repository.find_by_id(
            id_paquete_turistico
        )

        if tourist_package is None:
            raise LookupError("El paquete turístico no existe")

        return tourist_package

    def _ensure_city_exists(self, ciudad_id: int):
        city = self.city_repository.find_by_id(ciudad_id)

        if city is None:
            raise ValueError("La ciudad no existe")

    def _ensure_valid_dates(self, fecha_inicio, fecha_fin):
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha final no puede ser anterior a la fecha inicial")

    def _ensure_valid_package_status(self, estado: str):
        if estado not in ALLOWED_TOURIST_PACKAGE_STATUS:
            raise ValueError("Estado de paquete turístico no válido")

    def _ensure_products_are_valid(self, productos):
        product_ids = set()

        for product_data in productos:
            if product_data.producto_id in product_ids:
                raise ValueError("No puedes repetir productos dentro del mismo paquete")

            product_ids.add(product_data.producto_id)

            product = self.product_repository.find_by_id(product_data.producto_id)

            if product is None:
                raise ValueError("Uno de los productos no existe")

            if product.estado != PRODUCT_STATUS_ACTIVE:
                raise ValueError("Uno de los productos no está activo")

    def create_package(
        self,
        package_data: TouristPackageCreate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)
        self._ensure_city_exists(package_data.ciudad_id)
        self._ensure_valid_dates(
            package_data.fecha_inicio,
            package_data.fecha_fin
        )
        self._ensure_products_are_valid(package_data.productos)

        tourist_package = TouristPackageModel(
            nombre=package_data.nombre,
            descripcion=package_data.descripcion,
            precio=package_data.precio,
            descuento=package_data.descuento,
            estado=TOURIST_PACKAGE_STATUS_ACTIVE,
            fecha_inicio=package_data.fecha_inicio,
            fecha_fin=package_data.fecha_fin,
            cupo_max=package_data.cupo_max,
            ciudades_id_ciudad=package_data.ciudad_id
        )

        created_package = self.tourist_package_repository.create_package(
            tourist_package
        )

        for product_data in package_data.productos:
            self.tourist_package_repository.add_product_to_package(
                package_id=created_package.id_paquete_turistico,
                product_id=product_data.producto_id,
                cantidad=product_data.cantidad
            )

        return created_package

    def get_package_by_id(self, id_paquete_turistico: int):
        tourist_package = self._get_package_or_raise(id_paquete_turistico)

        if tourist_package.estado != TOURIST_PACKAGE_STATUS_ACTIVE:
            raise LookupError("El paquete turístico no existe o no está disponible")

        return tourist_package

    def get_package_by_id_admin(
        self,
        id_paquete_turistico: int,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)
        return self._get_package_or_raise(id_paquete_turistico)

    def list_active_packages(self):
        return self.tourist_package_repository.list_active_packages()

    def list_packages(self, current_user: UserModel):
        self._ensure_admin(current_user)
        return self.tourist_package_repository.list_packages()

    def list_active_packages_by_city(self, ciudad_id: int):
        self._ensure_city_exists(ciudad_id)
        return self.tourist_package_repository.list_active_by_city_id(ciudad_id)

    def update_package(
        self,
        id_paquete_turistico: int,
        package_data: TouristPackageUpdate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        tourist_package = self._get_package_or_raise(id_paquete_turistico)

        package_data_dict = package_data.model_dump(exclude_unset=True)

        if not package_data_dict:
            raise ValueError("No se enviaron datos para actualizar")

        if "ciudad_id" in package_data_dict:
            self._ensure_city_exists(package_data_dict["ciudad_id"])
            package_data_dict["ciudades_id_ciudad"] = package_data_dict.pop("ciudad_id")

        fecha_inicio = package_data_dict.get(
            "fecha_inicio",
            tourist_package.fecha_inicio
        )
        fecha_fin = package_data_dict.get(
            "fecha_fin",
            tourist_package.fecha_fin
        )

        self._ensure_valid_dates(fecha_inicio, fecha_fin)

        return self.tourist_package_repository.update_package(
            tourist_package,
            package_data_dict
        )

    def update_package_status(
        self,
        id_paquete_turistico: int,
        status_data: TouristPackageStatusUpdate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        tourist_package = self._get_package_or_raise(id_paquete_turistico)

        self._ensure_valid_package_status(status_data.estado)

        return self.tourist_package_repository.update_status(
            tourist_package,
            status_data.estado
        )
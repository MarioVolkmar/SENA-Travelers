# app/services/product_service.py

from sqlalchemy.orm import Session

from app.models.product_model import ProductModel
from app.models.provider_model import ProviderModel
from app.models.user_model import UserModel

from app.repositories.product_repository import ProductRepository
from app.repositories.city_repository import CityRepository
from app.repositories.provider_repository import ProviderRepository

from app.schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductProviderUpdate
)

from app.core.constants import (
    ADMIN_ROLE_ID,
    PROVIDER_ROLE_ID,
    PROVIDER_STATUS_APPROVED,
    PRODUCT_STATUS_ACTIVE,
    ALLOWED_PRODUCT_STATUS
)


class ProductService:
    def __init__(self, db: Session):
        self.product_repository = ProductRepository(db)
        self.city_repository = CityRepository(db)
        self.provider_repository = ProviderRepository(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_product_or_raise(self, id_producto: int):
        product = self.product_repository.find_by_id(id_producto)

        if product is None:
            raise LookupError("El producto no existe")

        return product

    def _get_provider_or_raise(self, id_proveedor: int):
        provider = self.provider_repository.find_by_id(id_proveedor)

        if provider is None:
            raise LookupError("El proveedor no existe")

        return provider

    def _get_provider_by_user_or_raise(self, usuario_id: int):
        provider = self.provider_repository.find_by_user_id(usuario_id)

        if provider is None:
            raise LookupError("El usuario no tiene perfil de proveedor")

        return provider

    def _ensure_city_exists(self, ciudad_id: int):
        city = self.city_repository.find_by_id(ciudad_id)

        if city is None:
            raise ValueError("La ciudad no existe")

    def _ensure_provider_approved(self, provider: ProviderModel):
        if provider.estado_verificacion != PROVIDER_STATUS_APPROVED:
            raise PermissionError("El proveedor no está aprobado")

    def _ensure_valid_product_status(self, estado: str):
        if estado not in ALLOWED_PRODUCT_STATUS:
            raise ValueError("Estado de producto no válido")

    def _ensure_admin_or_provider_owner(
        self,
        provider: ProviderModel,
        current_user: UserModel
    ):
        if current_user.rol_id == ADMIN_ROLE_ID:
            return

        if current_user.rol_id != PROVIDER_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

        own_provider = self._get_provider_by_user_or_raise(current_user.id_usuario)
        self._ensure_provider_approved(own_provider)

        if own_provider.id_proveedor != provider.id_proveedor:
            raise PermissionError("Solo puedes gestionar tus propios recursos")

    def _ensure_admin_or_product_owner_provider(
        self,
        product: ProductModel,
        current_user: UserModel
    ):
        if current_user.rol_id == ADMIN_ROLE_ID:
            return

        if current_user.rol_id != PROVIDER_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

        provider = self._get_provider_by_user_or_raise(current_user.id_usuario)
        self._ensure_provider_approved(provider)

        if product.proveedor_id != provider.id_proveedor:
            raise PermissionError("Solo puedes gestionar tus propios productos")

    def _resolve_provider_for_create(
        self,
        proveedor_id: int,
        current_user: UserModel
    ):
        provider = self._get_provider_or_raise(proveedor_id)
        self._ensure_provider_approved(provider)

        if current_user.rol_id == ADMIN_ROLE_ID:
            return provider

        if current_user.rol_id == PROVIDER_ROLE_ID:
            own_provider = self._get_provider_by_user_or_raise(current_user.id_usuario)
            self._ensure_provider_approved(own_provider)

            if own_provider.id_proveedor != provider.id_proveedor:
                raise PermissionError(
                    "Solo puedes crear productos para tu propio perfil proveedor"
                )

            return own_provider

        raise PermissionError("No tienes permisos para crear productos")

    def create_product(self, product_data: ProductCreate, current_user: UserModel):
        self._ensure_city_exists(product_data.ciudad_id)

        provider = self._resolve_provider_for_create(
            product_data.proveedor_id,
            current_user
        )

        product = ProductModel(
            nombre=product_data.nombre,
            descripcion=product_data.descripcion,
            tipo_producto=product_data.tipo_producto,
            costo=product_data.costo,
            ciudad_id=product_data.ciudad_id,
            proveedor_id=provider.id_proveedor,
            estado=PRODUCT_STATUS_ACTIVE
        )

        return self.product_repository.create_product(product)

    def get_product_by_id(self, id_producto: int):
        product = self._get_product_or_raise(id_producto)

        if product.estado != PRODUCT_STATUS_ACTIVE:
            raise LookupError("El producto no existe o no está disponible")

        return product

    def get_product_by_id_admin(self, id_producto: int, current_user: UserModel):
        self._ensure_admin(current_user)

        return self._get_product_or_raise(id_producto)

    def list_active_products(self):
        return self.product_repository.list_active_products()

    def list_products(self, current_user: UserModel):
        self._ensure_admin(current_user)

        return self.product_repository.list_products()

    def list_products_by_provider(self, proveedor_id: int, current_user: UserModel):
        provider = self._get_provider_or_raise(proveedor_id)

        self._ensure_admin_or_provider_owner(provider, current_user)

        return self.product_repository.list_by_provider_id(provider.id_proveedor)

    def list_products_by_city(self, ciudad_id: int):
        self._ensure_city_exists(ciudad_id)

        return self.product_repository.list_by_city_id(ciudad_id)

    def update_product(
        self,
        id_producto: int,
        product_data: ProductUpdate,
        current_user: UserModel
    ):
        product = self._get_product_or_raise(id_producto)

        self._ensure_admin_or_product_owner_provider(product, current_user)

        product_data_dict = product_data.model_dump(exclude_unset=True)

        if not product_data_dict:
            raise ValueError("No se enviaron datos para actualizar")

        if "ciudad_id" in product_data_dict:
            self._ensure_city_exists(product_data_dict["ciudad_id"])

        return self.product_repository.update_product(product, product_data_dict)

    def update_product_status(
        self,
        id_producto: int,
        status_data: ProductStatusUpdate,
        current_user: UserModel
    ):
        product = self._get_product_or_raise(id_producto)

        self._ensure_admin_or_product_owner_provider(product, current_user)
        self._ensure_valid_product_status(status_data.estado)

        return self.product_repository.update_status(product, status_data.estado)

    def update_product_provider(
        self,
        id_producto: int,
        provider_data: ProductProviderUpdate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        product = self._get_product_or_raise(id_producto)

        new_provider = self._get_provider_or_raise(provider_data.proveedor_id)
        self._ensure_provider_approved(new_provider)

        return self.product_repository.update_provider(
            product,
            new_provider.id_proveedor
        )
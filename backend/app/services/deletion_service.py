"""
Eliminaciones definitivas desde la consola del administrador.

Solo se permite borrar lo que no deja la base inconsistente ni hace perder
historial (reservas, pagos u órdenes de pago). En los demás casos se responde
con un mensaje que explica qué hacer (normalmente: desactivar en lugar de borrar).
"""
from sqlalchemy.orm import Session

from app.core import storage
from app.core.constants import ADMIN_ROLE_ID, PROVIDER_STATUS_REJECTED
from app.models.client_model import ClientModel
from app.models.notification_email_model import NotificationEmailModel
from app.models.product_model import ProductModel
from app.models.provider_model import ProviderModel
from app.models.provider_payment_order_model import (
    ProviderPaymentOrderItemModel,
    ProviderPaymentOrderModel,
)
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_image_model import TouristPackageImageModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.tourist_package_product_model import TouristPackageProductModel
from app.models.user_model import UserModel
from app.services.tourist_package_image_service import UPLOADED_KEY_PATTERN


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


class DeletionService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------------

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_or_raise(self, model, column, value, message):
        item = self.db.query(model).filter(column == value).first()

        if item is None:
            raise LookupError(message)

        return item

    def _count(self, model, *conditions) -> int:
        return self.db.query(model).filter(*conditions).count()

    def _commit(self):
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ---------------------------------------------------------------
    # Proveedor (solo rechazados)
    # ---------------------------------------------------------------

    def delete_provider(self, id_proveedor: int, current_user: UserModel):
        self._ensure_admin(current_user)
        provider = self._get_or_raise(
            ProviderModel, ProviderModel.id_proveedor, id_proveedor, "El proveedor no existe"
        )

        if provider.estado_verificacion != PROVIDER_STATUS_REJECTED:
            raise ValueError("Solo se pueden eliminar proveedores rechazados")

        products = self._count(ProductModel, ProductModel.proveedor_id == id_proveedor)
        if products:
            raise ValueError(
                f"El proveedor tiene {_plural(products, 'producto', 'productos')}. "
                "Elimínalos o asígnalos a otro proveedor primero."
            )

        orders = self._count(ProviderPaymentOrderModel, ProviderPaymentOrderModel.proveedor_id == id_proveedor)
        if orders:
            raise ValueError("El proveedor tiene órdenes de pago registradas; no se puede eliminar.")

        # La cuenta de usuario se conserva (sigue como cliente); solo se borra la solicitud
        self.db.delete(provider)
        self._commit()

    # ---------------------------------------------------------------
    # Paquete (sin reservas)
    # ---------------------------------------------------------------

    def delete_package(self, id_paquete: int, current_user: UserModel):
        self._ensure_admin(current_user)
        package = self._get_or_raise(
            TouristPackageModel,
            TouristPackageModel.id_paquete_turistico,
            id_paquete,
            "El paquete turístico no existe",
        )

        reservations = self._count(ReservationModel, ReservationModel.id_paquete_turistico == id_paquete)
        if reservations:
            raise ValueError(
                f"El paquete tiene {_plural(reservations, 'reserva', 'reservas')}. "
                "Desactívalo en lugar de eliminarlo para conservar el historial."
            )

        images = (
            self.db.query(TouristPackageImageModel)
            .filter(TouristPackageImageModel.paquete_id == id_paquete)
            .all()
        )
        uploaded_keys = [image.s3_key for image in images if UPLOADED_KEY_PATTERN.match(image.s3_key)]

        for image in images:
            self.db.delete(image)

        (
            self.db.query(TouristPackageProductModel)
            .filter(TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico == id_paquete)
            .delete(synchronize_session=False)
        )

        self.db.delete(package)
        self._commit()

        # Fotos subidas por la consola: también se borran del bucket (las cargadas a mano se conservan)
        for key in uploaded_keys:
            try:
                storage.delete_file(key)
            except Exception:
                pass

    # ---------------------------------------------------------------
    # Producto (sin paquetes ni órdenes)
    # ---------------------------------------------------------------

    def delete_product(self, id_producto: int, current_user: UserModel):
        self._ensure_admin(current_user)
        product = self._get_or_raise(
            ProductModel, ProductModel.id_producto, id_producto, "El producto no existe"
        )

        packages = self._count(
            TouristPackageProductModel, TouristPackageProductModel.productos_id_producto == id_producto
        )
        if packages:
            raise ValueError(
                f"El producto está incluido en {_plural(packages, 'paquete', 'paquetes')}. "
                "Quítalo de los paquetes o desactívalo."
            )

        order_lines = self._count(
            ProviderPaymentOrderItemModel, ProviderPaymentOrderItemModel.producto_id == id_producto
        )
        if order_lines:
            raise ValueError("El producto aparece en órdenes de pago; desactívalo en lugar de eliminarlo.")

        self.db.delete(product)
        self._commit()

    # ---------------------------------------------------------------
    # Usuario (sin reservas ni empresa con productos)
    # ---------------------------------------------------------------

    def delete_user(self, id_usuario: int, current_user: UserModel):
        self._ensure_admin(current_user)

        if id_usuario == current_user.id_usuario:
            raise ValueError("No puedes eliminar tu propia cuenta")

        user = self._get_or_raise(UserModel, UserModel.id_usuario, id_usuario, "El usuario no existe")

        client = self.db.query(ClientModel).filter(ClientModel.usuario_id == id_usuario).first()
        if client is not None:
            reservations = self._count(ReservationModel, ReservationModel.cliente_id == client.id_cliente)
            if reservations:
                raise ValueError(
                    f"El usuario tiene {_plural(reservations, 'reserva', 'reservas')}. "
                    "Desactívalo en lugar de eliminarlo."
                )

        provider = self.db.query(ProviderModel).filter(ProviderModel.usuario_id == id_usuario).first()
        if provider is not None:
            products = self._count(ProductModel, ProductModel.proveedor_id == provider.id_proveedor)
            orders = self._count(
                ProviderPaymentOrderModel, ProviderPaymentOrderModel.proveedor_id == provider.id_proveedor
            )
            if products or orders:
                raise ValueError(
                    "El usuario es proveedor con productos u órdenes de pago. Desactívalo en lugar de eliminarlo."
                )

        (
            self.db.query(NotificationEmailModel)
            .filter(NotificationEmailModel.usuarios_id_usuario == id_usuario)
            .delete(synchronize_session=False)
        )

        if client is not None:
            self.db.delete(client)

        if provider is not None:
            self.db.delete(provider)

        photo = user.foto_url
        self.db.delete(user)
        self._commit()

        if storage.is_avatar_key(photo):
            try:
                storage.delete_file(photo)
            except Exception:
                pass

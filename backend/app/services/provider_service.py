# app/services/provider_service.py

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.provider_model import ProviderModel
from app.models.user_model import UserModel

from app.repositories.provider_repository import ProviderRepository
from app.repositories.city_repository import CityRepository
from app.repositories.user_repository import UserRepository

from app.schemas.provider_schema import (
    ProviderCreate,
    ProviderUpdate,
    ProviderVerificationUpdate
)

from app.core.constants import (
    ADMIN_ROLE_ID,
    CLIENT_ROLE_ID,
    PROVIDER_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED,
    PROVIDER_STATUS_PENDING,
    PROVIDER_STATUS_APPROVED,
    PROVIDER_STATUS_REJECTED,
    ALLOWED_PROVIDER_VERIFICATION_STATUS
)


class ProviderService:
    def __init__(self, db: Session):
        self.provider_repository = ProviderRepository(db)
        self.city_repository = CityRepository(db)
        self.user_repository = UserRepository(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _ensure_user_email_verified(self, current_user: UserModel):
        if current_user.verificacion_email != EMAIL_VERIFICATION_VERIFIED:
            raise PermissionError("Debes verificar tu correo antes de solicitar ser proveedor")

    def _get_provider_or_raise(self, id_proveedor: int):
        provider = self.provider_repository.find_by_id(id_proveedor)

        if provider is None:
            raise LookupError("El proveedor no existe")

        return provider

    def _get_provider_or_raise_by_user_id(self, usuario_id: int):
        provider = self.provider_repository.find_by_user_id(usuario_id)

        if provider is None:
            raise LookupError("El proveedor no existe")

        return provider

    def _ensure_user_has_no_provider_profile(self, usuario_id: int):
        provider = self.provider_repository.find_by_user_id(usuario_id)

        if provider is not None:
            raise ValueError("El usuario ya tiene una solicitud o perfil de proveedor")

    def _ensure_rut_available(self, rut: str):
        provider = self.provider_repository.find_by_rut(rut)

        if provider is not None:
            raise ValueError("El RUT ya está registrado")

    def _ensure_city_exists(self, ciudad_id: int):
        city = self.city_repository.find_by_id(ciudad_id)

        if city is None:
            raise ValueError("La ciudad no existe")

    def _ensure_owner_or_admin(self, provider: ProviderModel, current_user: UserModel):
        is_owner = provider.usuario_id == current_user.id_usuario
        is_admin = current_user.rol_id == ADMIN_ROLE_ID

        if not is_owner and not is_admin:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _ensure_valid_verification_status(self, estado_verificacion: str):
        if estado_verificacion not in ALLOWED_PROVIDER_VERIFICATION_STATUS:
            raise ValueError("Estado de verificación no válido")

        if estado_verificacion == PROVIDER_STATUS_PENDING:
            raise ValueError(
                "La decisión administrativa solo puede ser aprobado o rechazado"
            )

    def create_provider(self, provider_data: ProviderCreate, current_user: UserModel):
        self._ensure_user_email_verified(current_user)
        self._ensure_user_has_no_provider_profile(current_user.id_usuario)
        self._ensure_rut_available(provider_data.rut)
        self._ensure_city_exists(provider_data.ciudad_id)

        provider = ProviderModel(
            usuario_id=current_user.id_usuario,
            rut=provider_data.rut,
            telefono=provider_data.telefono,
            direccion=provider_data.direccion,
            nombre_empresa=provider_data.nombre_empresa,
            ciudad_id=provider_data.ciudad_id,
            estado_verificacion=PROVIDER_STATUS_PENDING
        )

        return self.provider_repository.create_provider(provider)

    def get_provider_by_id(self, id_proveedor: int, current_user: UserModel):
        self._ensure_admin(current_user)
        return self._get_provider_or_raise(id_proveedor)

    def get_self_provider(self, current_user: UserModel):
        return self._get_provider_or_raise_by_user_id(current_user.id_usuario)

    def list_providers(self, current_user: UserModel):
        self._ensure_admin(current_user)
        return self.provider_repository.list_providers()

    def list_pending_providers(self, current_user: UserModel):
        self._ensure_admin(current_user)
        return self.provider_repository.list_pending_providers()

    def update_provider(
        self,
        id_proveedor: int,
        provider_data: ProviderUpdate,
        current_user: UserModel
    ):
        provider = self._get_provider_or_raise(id_proveedor)

        self._ensure_owner_or_admin(provider, current_user)

        provider_data_dict = provider_data.model_dump(exclude_unset=True)

        if not provider_data_dict:
            raise ValueError("No se enviaron datos para actualizar")

        if "ciudad_id" in provider_data_dict:
            self._ensure_city_exists(provider_data_dict["ciudad_id"])

        return self.provider_repository.update_provider(provider, provider_data_dict)

    def update_verification_status(
        self,
        id_proveedor: int,
        verification_data: ProviderVerificationUpdate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)
        self._ensure_valid_verification_status(
            verification_data.estado_verificacion
        )

        provider = self._get_provider_or_raise(id_proveedor)

        user = self.user_repository.find_by_id(provider.usuario_id)

        if user is None:
            raise LookupError("El usuario asociado al proveedor no existe")

        provider.fecha_verificacion = datetime.utcnow()

        if verification_data.estado_verificacion == PROVIDER_STATUS_APPROVED:
            self.user_repository.update_user_role(user, PROVIDER_ROLE_ID)

        if verification_data.estado_verificacion == PROVIDER_STATUS_REJECTED:
            self.user_repository.update_user_role(user, CLIENT_ROLE_ID)

        return self.provider_repository.update_verification_status(
            provider,
            verification_data.estado_verificacion
        )
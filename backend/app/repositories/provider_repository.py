from sqlalchemy.orm import Session

from app.models.provider_model import ProviderModel
from app.core.constants import PROVIDER_STATUS_PENDING


class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_provider(self, provider: ProviderModel):
        try:
            self.db.add(provider)
            self.db.commit()
            self.db.refresh(provider)

            return provider

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_proveedor: int):
        return (
            self.db.query(ProviderModel)
            .filter(ProviderModel.id_proveedor == id_proveedor)
            .first()
        )

    def find_by_user_id(self, usuario_id: int):
        return (
            self.db.query(ProviderModel)
            .filter(ProviderModel.usuario_id == usuario_id)
            .first()
        )

    def find_by_rut(self, rut: str):
        return (
            self.db.query(ProviderModel)
            .filter(ProviderModel.rut == rut)
            .first()
        )

    def list_providers(self):
        return self.db.query(ProviderModel).all()

    def list_pending_providers(self):
        return (
            self.db.query(ProviderModel)
            .filter(ProviderModel.estado_verificacion == PROVIDER_STATUS_PENDING)
            .all()
        )

    def update_provider(self, provider: ProviderModel, provider_data: dict):
        try:
            for field, value in provider_data.items():
                if value is not None:
                    setattr(provider, field, value)

            self.db.commit()
            self.db.refresh(provider)

            return provider

        except Exception as error:
            self.db.rollback()
            raise error

    def update_verification_status(
        self,
        provider: ProviderModel,
        estado_verificacion: str
    ):
        try:
            provider.estado_verificacion = estado_verificacion

            self.db.commit()
            self.db.refresh(provider)

            return provider

        except Exception as error:
            self.db.rollback()
            raise error
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import clock
from app.core.constants import (
    PRODUCT_STATUS_ACTIVE,
    PROVIDER_STATUS_APPROVED,
    RESERVATION_STATUS_CONFIRMED,
    RESERVATION_STATUS_PENDING,
)
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.tourist_package_product_model import TouristPackageProductModel
from app.models.user_model import UserModel
from app.repositories.product_repository import ProductRepository
from app.repositories.provider_repository import ProviderRepository


class ProviderDashboardService:
    """
    Datos del panel del proveedor: sus productos, los paquetes que los incluyen
    y cuántos viajeros hay reservados en esos paquetes.
    """

    def __init__(self, db: Session):
        self.db = db
        self.provider_repository = ProviderRepository(db)
        self.product_repository = ProductRepository(db)

    def get_dashboard(self, current_user: UserModel):
        provider = self.provider_repository.find_by_user_id(current_user.id_usuario)

        if provider is None:
            raise LookupError("No tienes una solicitud de proveedor")

        empty_summary = {"productos_activos": 0, "paquetes": 0, "viajeros_proximos": 0}

        # Mientras no esté aprobado solo ve el estado de su solicitud
        if provider.estado_verificacion != PROVIDER_STATUS_APPROVED:
            return {"proveedor": provider, "productos": [], "paquetes": [], "resumen": empty_summary}

        products = self.product_repository.list_by_provider_id(provider.id_proveedor)
        product_names = {product.id_producto: product.nombre for product in products}

        packages = []

        if product_names:
            links = (
                self.db.query(TouristPackageProductModel, TouristPackageModel)
                .join(
                    TouristPackageModel,
                    TouristPackageModel.id_paquete_turistico
                    == TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico,
                )
                .filter(TouristPackageProductModel.productos_id_producto.in_(product_names.keys()))
                .all()
            )

            by_package = {}

            for link, tourist_package in links:
                entry = by_package.setdefault(
                    tourist_package.id_paquete_turistico,
                    {"package": tourist_package, "productos": []},
                )
                entry["productos"].append(product_names[link.productos_id_producto])

            for package_id, entry in by_package.items():
                stats = (
                    self.db.query(
                        func.coalesce(func.sum(ReservationModel.cantidad_personas), 0),
                        func.count(ReservationModel.id_reserva),
                    )
                    .filter(
                        ReservationModel.id_paquete_turistico == package_id,
                        ReservationModel.estado == RESERVATION_STATUS_CONFIRMED,
                    )
                    .one()
                )
                pending_people = (
                    self.db.query(func.coalesce(func.sum(ReservationModel.cantidad_personas), 0))
                    .filter(
                        ReservationModel.id_paquete_turistico == package_id,
                        ReservationModel.estado == RESERVATION_STATUS_PENDING,
                    )
                    .scalar()
                )

                tourist_package = entry["package"]
                packages.append({
                    "id_paquete_turistico": package_id,
                    "nombre": tourist_package.nombre,
                    "ciudad_id": tourist_package.ciudades_id_ciudad,
                    "fecha_inicio": tourist_package.fecha_inicio,
                    "fecha_fin": tourist_package.fecha_fin,
                    "estado": tourist_package.estado,
                    "productos": sorted(entry["productos"]),
                    "viajeros_confirmados": int(stats[0] or 0),
                    "reservas_confirmadas": int(stats[1] or 0),
                    "viajeros_pendientes": int(pending_people or 0),
                })

        packages.sort(key=lambda item: item["fecha_inicio"])
        today = clock.today()

        summary = {
            "productos_activos": sum(1 for product in products if product.estado == PRODUCT_STATUS_ACTIVE),
            "paquetes": len(packages),
            "viajeros_proximos": sum(
                item["viajeros_confirmados"] for item in packages if item["fecha_fin"] >= today
            ),
        }

        return {"proveedor": provider, "productos": products, "paquetes": packages, "resumen": summary}

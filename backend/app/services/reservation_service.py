from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.reservation_model import ReservationModel
from app.models.user_model import UserModel

from app.repositories.reservation_repository import ReservationRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.tourist_package_repository import TouristPackageRepository

from app.services.companion_service import CompanionService
from app.services.notification_email_service import NotificationEmailService

from app.schemas.reservation_schema import (
    ReservationCreate,
    ReservationStatusUpdate
)

from app.core.constants import (
    ADMIN_ROLE_ID,
    RESERVATION_STATUS_PENDING,
    ALLOWED_RESERVATION_STATUS,
    TOURIST_PACKAGE_STATUS_ACTIVE
)


class ReservationService:
    def __init__(self, db: Session):
        self.reservation_repository = ReservationRepository(db)
        self.client_repository = ClientRepository(db)
        self.tourist_package_repository = TouristPackageRepository(db)
        self.companion_service = CompanionService(db)
        self.notification_email_service = NotificationEmailService(db)

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _get_reservation_or_raise(self, id_reserva: int):
        reservation = self.reservation_repository.find_by_id(id_reserva)

        if reservation is None:
            raise LookupError("La reserva no existe")

        return reservation

    def _get_client_profile_or_raise(self, current_user: UserModel):
        client = self.client_repository.find_by_user_id(
            current_user.id_usuario
        )

        if client is None:
            raise PermissionError("Debes tener un perfil de cliente para crear reservas")

        return client

    def _get_package_or_raise(self, id_paquete_turistico: int):
        tourist_package = self.tourist_package_repository.find_by_id(
            id_paquete_turistico
        )

        if tourist_package is None:
            raise LookupError("El paquete turístico no existe")

        return tourist_package

    def _ensure_package_is_active(self, tourist_package):
        if tourist_package.estado != TOURIST_PACKAGE_STATUS_ACTIVE:
            raise PermissionError("El paquete turístico no está disponible")

    def _ensure_reservation_date_is_valid(self, reservation_data, tourist_package):
        if reservation_data.fecha_reserva < tourist_package.fecha_inicio:
            raise ValueError("La fecha de reserva no puede ser anterior al inicio del paquete")

        if reservation_data.fecha_reserva > tourist_package.fecha_fin:
            raise ValueError("La fecha de reserva no puede ser posterior al final del paquete")

    def _ensure_valid_reservation_status(self, estado: str):
        if estado not in ALLOWED_RESERVATION_STATUS:
            raise ValueError("Estado de reserva no válido")

    def _ensure_owner_or_admin(
        self,
        reservation: ReservationModel,
        current_user: UserModel
    ):
        if current_user.rol_id == ADMIN_ROLE_ID:
            return

        client = self.client_repository.find_by_user_id(
            current_user.id_usuario
        )

        if client is None:
            raise PermissionError("No tienes permisos para realizar esta acción")

        if reservation.cliente_id != client.id_cliente:
            raise PermissionError("Solo puedes consultar tus propias reservas")

    def _generate_reservation_code(self):
        return f"RES-{uuid4().hex[:10].upper()}"

    def _calculate_total(self, tourist_package, cantidad_personas: int):
        precio = Decimal(tourist_package.precio)
        descuento = Decimal(tourist_package.descuento or 0)

        subtotal = precio * cantidad_personas

        if descuento > 0:
            discount_amount = subtotal * (descuento / Decimal(100))
            return subtotal - discount_amount

        return subtotal

    def create_reservation(
        self,
        reservation_data: ReservationCreate,
        current_user: UserModel
    ):
        client = self._get_client_profile_or_raise(current_user)

        tourist_package = self._get_package_or_raise(
            reservation_data.id_paquete_turistico
        )

        self._ensure_package_is_active(tourist_package)

        self._ensure_reservation_date_is_valid(
            reservation_data,
            tourist_package
        )

        total_reserva = self._calculate_total(
            tourist_package,
            reservation_data.cantidad_personas
        )

        reservation = ReservationModel(
            fecha_reserva=reservation_data.fecha_reserva,
            cantidad_personas=reservation_data.cantidad_personas,
            cliente_id=client.id_cliente,
            id_paquete_turistico=tourist_package.id_paquete_turistico,
            total_reserva=total_reserva,
            estado=RESERVATION_STATUS_PENDING,
            codigo_reserva=self._generate_reservation_code()
        )

        created_reservation = self.reservation_repository.create_reservation(
            reservation
        )

        self.companion_service.create_many_companions(
            companions_data=reservation_data.acompanantes,
            reserva_id=created_reservation.id_reserva,
            cantidad_personas=reservation_data.cantidad_personas
        )

        self.notification_email_service.create_reservation_confirmation_email(
            user=current_user,
            reservation=created_reservation
        )

        return created_reservation

    def get_reservation_by_id(
        self,
        id_reserva: int,
        current_user: UserModel
    ):
        reservation = self._get_reservation_or_raise(id_reserva)

        self._ensure_owner_or_admin(reservation, current_user)

        return reservation

    def list_my_reservations(self, current_user: UserModel):
        client = self._get_client_profile_or_raise(current_user)

        return self.reservation_repository.list_by_client_id(
            client.id_cliente
        )

    def list_reservations(self, current_user: UserModel):
        self._ensure_admin(current_user)

        return self.reservation_repository.list_reservations()

    def update_reservation_status(
        self,
        id_reserva: int,
        status_data: ReservationStatusUpdate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)

        reservation = self._get_reservation_or_raise(id_reserva)

        self._ensure_valid_reservation_status(status_data.estado)

        return self.reservation_repository.update_status(
            reservation,
            status_data.estado
        )
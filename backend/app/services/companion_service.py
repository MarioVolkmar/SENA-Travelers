from app.models.companion_model import CompanionModel

from app.repositories.companion_repository import CompanionRepository

from app.schemas.companion_schema import CompanionCreate


class CompanionService:
    def __init__(self, db):
        self.companion_repository = CompanionRepository(db)

    def _get_companion_or_raise(self, id_acompanante: int):
        companion = self.companion_repository.find_by_id(id_acompanante)

        if companion is None:
            raise LookupError("El acompañante no existe")

        return companion

    def _ensure_valid_companion_count(
        self,
        companions: list[CompanionCreate],
        cantidad_personas: int
    ):
        max_companions = cantidad_personas - 1

        if len(companions) > max_companions:
            raise ValueError(
                "La cantidad de acompañantes no puede superar la cantidad de personas de la reserva"
            )

    def create_companion(
        self,
        companion_data: CompanionCreate,
        reserva_id: int
    ):
        companion = CompanionModel(
            nombre=companion_data.nombre,
            documento=companion_data.documento,
            fecha_nacimiento=companion_data.fecha_nacimiento,
            reserva_id=reserva_id
        )

        return self.companion_repository.create_companion(companion)

    def create_many_companions(
        self,
        companions_data: list[CompanionCreate],
        reserva_id: int,
        cantidad_personas: int
    ):
        self._ensure_valid_companion_count(
            companions_data,
            cantidad_personas
        )

        companions = []

        for companion_data in companions_data:
            companion = CompanionModel(
                nombre=companion_data.nombre,
                documento=companion_data.documento,
                fecha_nacimiento=companion_data.fecha_nacimiento,
                reserva_id=reserva_id
            )

            companions.append(companion)

        return self.companion_repository.create_many_companions(companions)

    def list_companions_by_reservation(self, reserva_id: int):
        return self.companion_repository.list_by_reservation_id(reserva_id)
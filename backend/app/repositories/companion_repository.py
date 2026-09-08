from sqlalchemy.orm import Session

from app.models.companion_model import CompanionModel


class CompanionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_companion(self, companion: CompanionModel):
        try:
            self.db.add(companion)
            self.db.commit()
            self.db.refresh(companion)
            return companion

        except Exception as error:
            self.db.rollback()
            raise error

    def create_many_companions(self, companions: list[CompanionModel]):
        try:
            self.db.add_all(companions)
            self.db.commit()

            for companion in companions:
                self.db.refresh(companion)

            return companions

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_acompanante: int):
        return (
            self.db.query(CompanionModel)
            .filter(CompanionModel.id_acompanante == id_acompanante)
            .first()
        )

    def list_by_reservation_id(self, reserva_id: int):
        return (
            self.db.query(CompanionModel)
            .filter(CompanionModel.reserva_id == reserva_id)
            .all()
        )
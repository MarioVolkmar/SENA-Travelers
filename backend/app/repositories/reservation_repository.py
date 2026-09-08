from sqlalchemy.orm import Session

from app.models.reservation_model import ReservationModel


class ReservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_reservation(self, reservation: ReservationModel):
        try:
            self.db.add(reservation)
            self.db.commit()
            self.db.refresh(reservation)
            return reservation

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_reserva: int):
        return (
            self.db.query(ReservationModel)
            .filter(ReservationModel.id_reserva == id_reserva)
            .first()
        )

    def find_by_code(self, codigo_reserva: str):
        return (
            self.db.query(ReservationModel)
            .filter(ReservationModel.codigo_reserva == codigo_reserva)
            .first()
        )

    def list_reservations(self):
        return self.db.query(ReservationModel).all()

    def list_by_client_id(self, cliente_id: int):
        return (
            self.db.query(ReservationModel)
            .filter(ReservationModel.cliente_id == cliente_id)
            .all()
        )

    def update_status(self, reservation: ReservationModel, estado: str):
        try:
            reservation.estado = estado

            self.db.commit()
            self.db.refresh(reservation)

            return reservation

        except Exception as error:
            self.db.rollback()
            raise error 
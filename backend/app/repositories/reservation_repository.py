from sqlalchemy import func
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

    def count_reserved_people(self, id_paquete_turistico: int, excluded_status: str):
        """Suma las personas de las reservas de un paquete que no estén en excluded_status."""
        total = (
            self.db.query(func.coalesce(func.sum(ReservationModel.cantidad_personas), 0))
            .filter(
                ReservationModel.id_paquete_turistico == id_paquete_turistico,
                ReservationModel.estado != excluded_status
            )
            .scalar()
        )

        return int(total or 0)

    def cancel(self, reservation: ReservationModel, estado: str, fecha_cancelacion, penalidad, reembolso):
        try:
            reservation.estado = estado
            reservation.fecha_cancelacion = fecha_cancelacion
            reservation.penalidad_cancelacion = penalidad
            reservation.reembolso = reembolso

            self.db.commit()
            self.db.refresh(reservation)

            return reservation

        except Exception as error:
            self.db.rollback()
            raise error

    def update_status(self, reservation: ReservationModel, estado: str):
        try:
            reservation.estado = estado

            self.db.commit()
            self.db.refresh(reservation)

            return reservation

        except Exception as error:
            self.db.rollback()
            raise error 
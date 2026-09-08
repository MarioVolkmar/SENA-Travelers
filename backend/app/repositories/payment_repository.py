from sqlalchemy.orm import Session

from app.models.payment_model import PaymentModel
from app.models.reservation_model import ReservationModel


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_payment(self, payment: PaymentModel):
        try:
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            return payment

        except Exception as error:
            self.db.rollback()
            raise error

    def list_by_client_id(self, cliente_id: int):
        return (
            self.db.query(PaymentModel)
            .join(
                ReservationModel,
                PaymentModel.reserva_id == ReservationModel.id_reserva
            )
            .filter(ReservationModel.cliente_id == cliente_id)
            .all()
        )

    def find_by_id(self, id_pago: int):
        return (
            self.db.query(PaymentModel)
            .filter(PaymentModel.id_pago == id_pago)
            .first()
        )

    def find_by_reservation_id(self, reserva_id: int):
        return (
            self.db.query(PaymentModel)
            .filter(PaymentModel.reserva_id == reserva_id)
            .first()
        )

    def find_by_reference(self, referencia_pago: str):
        return (
            self.db.query(PaymentModel)
            .filter(PaymentModel.referencia_pago == referencia_pago)
            .first()
        )

    def list_payments(self):
        return self.db.query(PaymentModel).all()

    def list_by_reservation_id(self, reserva_id: int):
        return (
            self.db.query(PaymentModel)
            .filter(PaymentModel.reserva_id == reserva_id)
            .all()
        )
    
    
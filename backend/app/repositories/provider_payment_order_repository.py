from sqlalchemy.orm import Session

from app.models.provider_payment_order_model import ProviderPaymentOrderModel


class ProviderPaymentOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order: ProviderPaymentOrderModel):
        try:
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            return order

        except Exception as error:
            self.db.rollback()
            raise error

    def save(self, order: ProviderPaymentOrderModel):
        try:
            self.db.commit()
            self.db.refresh(order)
            return order

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_orden: int):
        return (
            self.db.query(ProviderPaymentOrderModel)
            .filter(ProviderPaymentOrderModel.id_orden == id_orden)
            .first()
        )

    def find_by_provider_and_reservation(self, proveedor_id: int, reserva_id: int):
        return (
            self.db.query(ProviderPaymentOrderModel)
            .filter(
                ProviderPaymentOrderModel.proveedor_id == proveedor_id,
                ProviderPaymentOrderModel.reserva_id == reserva_id,
            )
            .first()
        )

    def list_by_reservation(self, reserva_id: int):
        return (
            self.db.query(ProviderPaymentOrderModel)
            .filter(ProviderPaymentOrderModel.reserva_id == reserva_id)
            .all()
        )

    def list_orders(self, estado=None, proveedor_id=None):
        query = self.db.query(ProviderPaymentOrderModel)

        if estado:
            query = query.filter(ProviderPaymentOrderModel.estado == estado)

        if proveedor_id:
            query = query.filter(ProviderPaymentOrderModel.proveedor_id == proveedor_id)

        return query.order_by(ProviderPaymentOrderModel.id_orden.desc()).all()

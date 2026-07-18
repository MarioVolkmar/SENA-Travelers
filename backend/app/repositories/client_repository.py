from sqlalchemy.orm import Session

from app.models.client_model import ClientModel


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_client(self, client: ClientModel):
        try:
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            return client

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_cliente: int):
        return (
            self.db.query(ClientModel)
            .filter(ClientModel.id_cliente == id_cliente)
            .first()
        )

    def list_clients(self):
        return self.db.query(ClientModel).all()
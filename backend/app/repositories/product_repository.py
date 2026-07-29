from sqlalchemy.orm import Session

from app.models.product_model import ProductModel


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, product: ProductModel):
        try:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)

            return product

        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_producto: int):
        return (
            self.db.query(ProductModel)
            .filter(ProductModel.id_producto == id_producto)
            .first()
        )

    def list_products(self):
        return self.db.query(ProductModel).all()

    def list_active_products(self):
        return (
            self.db.query(ProductModel)
            .filter(ProductModel.estado == "activo")
            .all()
        )

    def list_by_provider_id(self, proveedor_id: int):
        return (
            self.db.query(ProductModel)
            .filter(ProductModel.proveedor_id == proveedor_id)
            .all()
        )

    def list_by_city_id(self, ciudad_id: int):
        return (
            self.db.query(ProductModel)
            .filter(ProductModel.ciudad_id == ciudad_id)
            .all()
        )

    def update_product(self, product: ProductModel, product_data: dict):
        try:
            for field, value in product_data.items():
                if value is not None:
                    setattr(product, field, value)

            self.db.commit()
            self.db.refresh(product)

            return product

        except Exception as error:
            self.db.rollback()
            raise error

    def update_status(self, product: ProductModel, estado: str):
        try:
            product.estado = estado

            self.db.commit()
            self.db.refresh(product)

            return product

        except Exception as error:
            self.db.rollback()
            raise error

    def update_provider(self, product: ProductModel, proveedor_id: int):
        try:
            product.proveedor_id = proveedor_id

            self.db.commit()
            self.db.refresh(product)

            return product

        except Exception as error:
            self.db.rollback()
            raise error
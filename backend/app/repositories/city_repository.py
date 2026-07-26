from sqlalchemy.orm import Session

from app.models.city_model import CityModel

class CityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_city(self, city: CityModel):
        try:
            self.db.add(city)
            self.db.commit()
            self.db.refresh(city)
            return city
        
        except Exception as error:
            self.db.rollback()
            raise error

    def find_by_id(self, id_ciudad: int):
        return (
            self.db.query(CityModel)
            .filter(CityModel.id_ciudad == id_ciudad)
            .first()
        )

    def list_cities(self):
        return self.db.query(CityModel).all()
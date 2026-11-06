from sqlalchemy.orm import Session

from app.models.setting_model import SettingModel


class SettingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, clave: str):
        return self.db.query(SettingModel).filter(SettingModel.clave == clave).first()

    def set(self, clave: str, valor: str):
        try:
            setting = self.get(clave)

            if setting is None:
                setting = SettingModel(clave=clave, valor=valor)
                self.db.add(setting)
            else:
                setting.valor = valor

            self.db.commit()
            return setting

        except Exception as error:
            self.db.rollback()
            raise error

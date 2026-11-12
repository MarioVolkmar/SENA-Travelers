from sqlalchemy.orm import Session

from app.core.constants import (
    ADMIN_ROLE_ID,
    DEFAULT_SETTINGS,
    SETTING_CANCELLATION_FREE_DAYS,
    SETTING_CANCELLATION_PENALTY_PERCENT,
    SETTING_PAYMENT_HOURS,
    SETTING_PROVIDER_PAYMENT_DAY,
    SETTING_PROVIDER_PAYMENT_DAYS,
    SETTING_REMINDER_DAYS,
)
from app.models.user_model import UserModel
from app.repositories.setting_repository import SettingRepository

EDITABLE_SETTINGS = (
    SETTING_PROVIDER_PAYMENT_DAYS,
    SETTING_CANCELLATION_FREE_DAYS,
    SETTING_CANCELLATION_PENALTY_PERCENT,
    SETTING_REMINDER_DAYS,
    SETTING_PAYMENT_HOURS,
    SETTING_PROVIDER_PAYMENT_DAY,
)


class SettingService:
    """Configuración del sistema que el administrador puede cambiar desde la consola."""

    def __init__(self, db: Session):
        self.repository = SettingRepository(db)

    def get_value(self, clave: str) -> str:
        setting = self.repository.get(clave)
        return setting.valor if setting is not None else DEFAULT_SETTINGS[clave]

    def get_int(self, clave: str) -> int:
        return int(self.get_value(clave))

    def provider_payment_days(self) -> int:
        return self.get_int(SETTING_PROVIDER_PAYMENT_DAYS)

    def cancellation_free_days(self) -> int:
        return self.get_int(SETTING_CANCELLATION_FREE_DAYS)

    def cancellation_penalty_percent(self) -> int:
        return self.get_int(SETTING_CANCELLATION_PENALTY_PERCENT)

    def reminder_days(self) -> int:
        return self.get_int(SETTING_REMINDER_DAYS)

    def provider_payment_day(self) -> int:
        return self.get_int(SETTING_PROVIDER_PAYMENT_DAY)

    def payment_hours(self) -> int:
        return self.get_int(SETTING_PAYMENT_HOURS)

    def all_settings(self):
        return {clave: self.get_int(clave) for clave in EDITABLE_SETTINGS}

    def get_settings(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

        return self.all_settings()

    def update_settings(self, data: dict, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

        for clave in EDITABLE_SETTINGS:
            if data.get(clave) is not None:
                self.repository.set(clave, str(data[clave]))

        return self.get_settings(current_user)

import os
from datetime import date
from dotenv import load_dotenv

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.connection import get_db

# Importar modelos para que SQLAlchemy conozca todas las tablas
from app.models.role_model import RoleModel
from app.models.user_model import UserModel
from app.models.city_model import CityModel
from app.models.client_model import ClientModel
from app.models.provider_model import ProviderModel
from app.models.product_model import ProductModel
from app.models.notification_email_model import NotificationEmailModel
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.tourist_package_product_model import TouristPackageProductModel
from app.models.companion_model import CompanionModel
from app.models.payment_model import PaymentModel
from app.models.tourist_package_image_model import TouristPackageImageModel
from app.models.provider_payment_order_model import ProviderPaymentOrderModel, ProviderPaymentOrderItemModel
from app.models.setting_model import SettingModel
from app.models.audit_log_model import AuditLogModel
from app.models.app_notification_model import AppNotificationModel
from app.models.favorite_model import FavoriteModel
from app.models.review_model import ReviewModel
from app.models.coupon_model import CouponModel

load_dotenv()
os.environ["EMAILS_ENABLED"] = "false"
os.environ["REMINDERS_ENABLED"] = "false"
os.environ["GEOCODING_ENABLED"] = "false"  # los tests no salen a internet

TEST_DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_TEST_NAME"),
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    # Datos base necesarios
    db.add_all([
        RoleModel(id_rol=1, descripcion="administrador"),
        RoleModel(id_rol=2, descripcion="cliente"),
        RoleModel(id_rol=3, descripcion="proveedor"),
    ])

    db.add_all([
        CityModel(id_ciudad=1, nombre="Medellín", departamento="Antioquia", pais="Colombia"),
        CityModel(id_ciudad=2, nombre="Cartagena", departamento="Bolívar", pais="Colombia"),
    ])

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fecha "de hoy" fija para las reglas que dependen del calendario (cancelaciones).
# Los paquetes de prueba viajan del 10 al 12 de septiembre de 2026.
FROZEN_TODAY = date(2026, 8, 1)


@pytest.fixture(autouse=True)
def reset_login_limiter():
    """Cada prueba empieza sin intentos fallidos de inicio de sesión acumulados."""
    from app.core import login_limiter

    login_limiter.reset_all()
    yield
    login_limiter.reset_all()


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    """Fija la fecha actual de la app (app.core.clock); el test puede moverla con frozen_today(fecha)."""
    from app.core import clock

    state = {"today": FROZEN_TODAY}
    monkeypatch.setattr(clock, "today", lambda: state["today"])

    def set_today(new_date):
        state["today"] = new_date

    return set_today
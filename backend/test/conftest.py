import os
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

load_dotenv()

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
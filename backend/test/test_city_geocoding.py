from decimal import Decimal

import pytest

from app.routes import city_routes
from test_reservations import create_admin_with_token


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_geocoder(monkeypatch):
    calls = []

    def fake(nombre, departamento, pais="Colombia"):
        calls.append((nombre, departamento, pais))
        if nombre == "Ciudad Perdida":
            return None
        return Decimal("6.267500"), Decimal("-75.568500")

    monkeypatch.setattr(city_routes, "find_coordinates", fake)
    return calls


def test_new_city_gets_coordinates_automatically(client, db_session, fake_geocoder):
    _, admin_token = create_admin_with_token(client, db_session)

    response = client.post("/cities/", json={"nombre": "Guatapé", "departamento": "Antioquia"}, headers=auth(admin_token))

    assert response.status_code == 201, response.json()
    assert response.json()["latitud"] == pytest.approx(6.2675)
    assert response.json()["longitud"] == pytest.approx(-75.5685)
    assert fake_geocoder == [("Guatapé", "Antioquia", "Colombia")]


def test_manual_coordinates_are_respected(client, db_session, fake_geocoder):
    _, admin_token = create_admin_with_token(client, db_session)

    response = client.post(
        "/cities/",
        json={"nombre": "Capurganá", "departamento": "Chocó", "latitud": 8.63, "longitud": -77.35},
        headers=auth(admin_token),
    )

    assert response.json()["latitud"] == pytest.approx(8.63)
    assert fake_geocoder == []  # no se consultó el servicio


def test_city_is_created_even_if_location_is_not_found(client, db_session, fake_geocoder):
    _, admin_token = create_admin_with_token(client, db_session)

    response = client.post("/cities/", json={"nombre": "Ciudad Perdida", "departamento": "Magdalena"}, headers=auth(admin_token))

    assert response.status_code == 201
    assert response.json()["latitud"] is None


def test_recalculate_location_on_edit(client, db_session, fake_geocoder):
    _, admin_token = create_admin_with_token(client, db_session)
    city = client.post("/cities/", json={"nombre": "Ciudad Perdida", "departamento": "Magdalena"}, headers=auth(admin_token)).json()

    failed = client.patch(f"/cities/{city['id_ciudad']}", json={"recalcular_ubicacion": True}, headers=auth(admin_token))
    assert failed.status_code == 400

    renamed = client.patch(
        f"/cities/{city['id_ciudad']}",
        json={"nombre": "Ciénaga", "recalcular_ubicacion": True},
        headers=auth(admin_token),
    )
    assert renamed.status_code == 200
    assert renamed.json()["nombre"] == "Ciénaga"
    assert renamed.json()["latitud"] == pytest.approx(6.2675)

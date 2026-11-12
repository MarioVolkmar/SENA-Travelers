"""
Reglas de fechas de los paquetes y edades mínimas.
La fecha "de hoy" en las pruebas es el 1 de agosto de 2026 (conftest.FROZEN_TODAY).
"""
from datetime import date

from app.core import clock
from app.models.reservation_model import ReservationModel

from test_packages import create_admin_with_token, create_approved_provider_with_product, create_package
from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
)
from test_payments import create_verified_user, login_user


# ------------------------------------------------------------------ edad

def test_age_on_counts_only_completed_years():
    assert clock.age_on(date(2008, 8, 2), date(2026, 8, 1)) == 17   # cumple mañana
    assert clock.age_on(date(2008, 8, 1), date(2026, 8, 1)) == 18   # cumple hoy
    assert clock.age_on(date(2000, 2, 29), date(2026, 2, 28)) == 25


# ------------------------------------------------------------------ fechas de paquetes

def admin_and_product(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)
    _, product = create_approved_provider_with_product(client, db_session, admin_token)
    return admin_token, product["id_producto"]


def test_cannot_create_package_starting_in_the_past(client, db_session):
    admin_token, product_id = admin_and_product(client, db_session)

    response = create_package(client, admin_token, product_id, fecha_inicio="2026-07-20", fecha_fin="2026-07-25")

    assert response.status_code == 400
    assert "anterior a hoy" in response.json()["detail"]


def test_cannot_create_package_ending_before_it_starts(client, db_session):
    admin_token, product_id = admin_and_product(client, db_session)

    response = create_package(client, admin_token, product_id, fecha_inicio="2026-09-12", fecha_fin="2026-09-10")

    assert response.status_code == 400
    assert "fecha final" in response.json()["detail"]


def test_package_can_start_today(client, db_session):
    admin_token, product_id = admin_and_product(client, db_session)

    response = create_package(client, admin_token, product_id, fecha_inicio="2026-08-01", fecha_fin="2026-08-05")

    assert response.status_code == 201, response.json()


def test_editing_a_started_package_keeps_its_original_start(client, db_session, frozen_today):
    admin_token, product_id = admin_and_product(client, db_session)
    package = create_package(client, admin_token, product_id, fecha_inicio="2026-09-10", fecha_fin="2026-09-20").json()
    frozen_today(date(2026, 9, 15))  # el paquete ya empezó

    # Se edita el nombre enviando las mismas fechas (como hace el formulario): debe funcionar
    same_dates = client.patch(
        f"/packages/{package['id_paquete_turistico']}",
        json={"nombre": "Nuevo nombre", "fecha_inicio": "2026-09-10", "fecha_fin": "2026-09-20"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert same_dates.status_code == 200, same_dates.json()

    # Pero no se puede mover el inicio a otra fecha pasada
    moved = client.patch(
        f"/packages/{package['id_paquete_turistico']}",
        json={"fecha_inicio": "2026-09-12"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert moved.status_code == 400


# ------------------------------------------------------------------ edad del viajero

def client_profile(client, token, fecha_nacimiento, identificacion="555000111"):
    return client.post(
        "/clients/me",
        json={"identificacion": identificacion, "fecha_nacimiento": fecha_nacimiento, "ciudad_id": 1},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_minor_cannot_create_traveler_card(client, db_session):
    create_verified_user(client, db_session, nombre="Menor", email="menor@example.com")
    token = login_user(client, "menor@example.com")

    response = client_profile(client, token, "2008-08-02")  # cumple 18 mañana

    assert response.status_code == 400
    assert "18" in response.json()["detail"]


def test_traveler_who_turns_18_today_can_create_card(client, db_session):
    create_verified_user(client, db_session, nombre="Recien Mayor", email="mayor@example.com")
    token = login_user(client, "mayor@example.com")

    response = client_profile(client, token, "2008-08-01")

    assert response.status_code == 201, response.json()


# ------------------------------------------------------------------ edad de los acompañantes

def test_companion_younger_than_7_on_trip_date_is_rejected(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    token, _ = create_client_with_token(client, db_session, email="papa@example.com", identificacion="556000111")

    # Viaje el 10 de septiembre de 2026: cumple 7 años el 11 de septiembre
    response = create_reservation(
        client, token, package_id=package["id_paquete_turistico"], cantidad_personas=2,
        acompanantes=[{"nombre": "Niña", "documento": "110011", "fecha_nacimiento": "2019-09-11"}],
    )

    assert response.status_code == 400
    assert "7 años" in response.json()["detail"]
    db_session.rollback()
    assert db_session.query(ReservationModel).count() == 0  # no queda reserva a medias


def test_companion_who_is_7_on_trip_date_is_accepted(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    token, _ = create_client_with_token(client, db_session, email="mama@example.com", identificacion="557000111")

    response = create_reservation(
        client, token, package_id=package["id_paquete_turistico"], cantidad_personas=2,
        acompanantes=[{"nombre": "Niño", "documento": "120012", "fecha_nacimiento": "2019-09-10"}],
    )

    assert response.status_code == 201, response.json()

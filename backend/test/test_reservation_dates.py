from datetime import date

from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
)

# Paquete de prueba: del 2026-09-10 al 2026-09-12


def setup(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    token, _ = create_client_with_token(
        client, db_session, email="cliente_fechas@example.com", identificacion="920920920"
    )
    return package, token


def test_cannot_reserve_a_date_that_already_passed(client, db_session, frozen_today):
    package, token = setup(client, db_session)
    frozen_today(date(2026, 9, 11))

    response = create_reservation(client, token, package["id_paquete_turistico"], fecha_reserva="2026-09-10")

    assert response.status_code == 400
    assert "a partir de mañana" in response.json()["detail"]


def test_cannot_reserve_for_today(client, db_session, frozen_today):
    package, token = setup(client, db_session)
    frozen_today(date(2026, 9, 10))

    response = create_reservation(client, token, package["id_paquete_turistico"], fecha_reserva="2026-09-10")

    assert response.status_code == 400


def test_can_reserve_from_tomorrow_inside_package_dates(client, db_session, frozen_today):
    package, token = setup(client, db_session)
    frozen_today(date(2026, 9, 10))

    response = create_reservation(client, token, package["id_paquete_turistico"], fecha_reserva="2026-09-11")

    assert response.status_code == 201, response.json()


def test_public_catalog_hides_finished_packages(client, db_session, frozen_today):
    package, _ = setup(client, db_session)
    package_id = package["id_paquete_turistico"]

    frozen_today(date(2026, 9, 11))  # aún queda el 12 de septiembre
    assert package_id in [item["id_paquete_turistico"] for item in client.get("/packages/").json()]
    assert package_id in [item["id_paquete_turistico"] for item in client.get("/packages/city/1").json()]

    frozen_today(date(2026, 9, 12))  # último día: ya no se puede reservar
    assert package_id not in [item["id_paquete_turistico"] for item in client.get("/packages/").json()]
    assert package_id not in [item["id_paquete_turistico"] for item in client.get("/packages/city/1").json()]


def test_finished_package_detail_is_still_visible(client, db_session, frozen_today):
    """Las reservas antiguas siguen enlazando a su paquete aunque ya haya terminado."""
    package, _ = setup(client, db_session)
    frozen_today(date(2026, 10, 1))

    response = client.get(f"/packages/{package['id_paquete_turistico']}")

    assert response.status_code == 200

from app.models.reservation_model import ReservationModel

from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
)


def test_list_cities_is_public(client):
    response = client.get("/cities/")

    assert response.status_code == 200
    assert {city["nombre"] for city in response.json()} >= {"Medellín", "Cartagena"}


def test_too_many_companions_does_not_leave_orphan_reservation(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(
        client, db_session, email="cliente_huerfana@example.com", identificacion="800800800"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"],
        cantidad_personas=1
    )

    assert response.status_code == 400
    db_session.expire_all()
    assert db_session.query(ReservationModel).count() == 0


def test_cannot_reserve_more_people_than_available_slots(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(
        client, db_session, email="cliente_cupo@example.com", identificacion="810810810"
    )
    package_id = package["id_paquete_turistico"]

    # Máximo 10 viajeros por reserva: 10 + 5 ocupan 15 de los 20 cupos
    first = create_reservation(client, client_token, package_id, cantidad_personas=10, acompanantes=[])
    assert first.status_code == 201, first.json()
    extra = create_reservation(client, client_token, package_id, cantidad_personas=5, acompanantes=[])
    assert extra.status_code == 201, extra.json()

    availability = client.get(f"/reservations/availability/{package_id}").json()
    assert availability == {"id_paquete_turistico": package_id, "cupo_max": 20, "cupos_disponibles": 5}

    second = create_reservation(client, client_token, package_id, cantidad_personas=6, acompanantes=[])
    assert second.status_code == 400
    assert "cupo" in second.json()["detail"].lower()


def test_client_can_cancel_own_pending_reservation_and_frees_slots(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(
        client, db_session, email="cliente_cancela@example.com", identificacion="820820820"
    )
    package_id = package["id_paquete_turistico"]
    headers = {"Authorization": f"Bearer {client_token}"}

    reservation = create_reservation(client, client_token, package_id, cantidad_personas=10, acompanantes=[]).json()

    response = client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["estado"] == "cancelada"

    availability = client.get(f"/reservations/availability/{package_id}").json()
    assert availability["cupos_disponibles"] == 20

    again = client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=headers)
    assert again.status_code == 400


def test_client_cannot_cancel_other_client_reservation(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    owner_token, _ = create_client_with_token(
        client, db_session, email="cliente_duenio@example.com", identificacion="830830830"
    )
    other_token, _ = create_client_with_token(
        client, db_session, email="cliente_otro@example.com", identificacion="840840840"
    )

    reservation = create_reservation(
        client, owner_token, package["id_paquete_turistico"], cantidad_personas=1, acompanantes=[]
    ).json()

    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/cancel",
        headers={"Authorization": f"Bearer {other_token}"}
    )

    assert response.status_code == 403

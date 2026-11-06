from decimal import Decimal

from app.models.user_model import UserModel

from test_payments import create_client_with_reservation, create_package_ready_for_payment, create_payment
from test_reservations import create_client_with_token, login_user


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def user_id(db_session, email):
    db_session.rollback()
    return db_session.query(UserModel).filter(UserModel.email == email).first().id_usuario


def test_admin_sees_full_client_overview(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)
    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="ficha_cliente@example.com",
        identificacion="700700700",
    )
    assert create_payment(client, client_token, reservation["id_reserva"], valor=reservation["total_reserva"]).status_code == 201

    response = client.get(f"/users/{user_id(db_session, 'ficha_cliente@example.com')}/overview", headers=auth(admin_token))

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["usuario"]["email"] == "ficha_cliente@example.com"
    assert "contrasena" not in data["usuario"]
    assert data["cliente"]["identificacion"] == "700700700"
    assert data["proveedor"] is None

    assert len(data["reservas"]) == 1
    item = data["reservas"][0]
    assert item["paquete"] == package["nombre"]
    assert item["estado"] == "confirmada"
    assert len(item["acompanantes"]) == 1

    assert len(data["pagos"]) == 1
    assert data["notificaciones"], "debe incluir los correos enviados"
    assert data["resumen"]["reservas"] == 1
    assert data["resumen"]["reservas_confirmadas"] == 1
    assert Decimal(data["resumen"]["total_pagado"]) == Decimal(reservation["total_reserva"])


def test_overview_of_provider_includes_products_and_orders(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)
    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="ficha_cliente2@example.com",
        identificacion="710710710",
    )
    create_payment(client, client_token, reservation["id_reserva"], valor=reservation["total_reserva"])

    providers = client.get("/providers/", headers=auth(admin_token)).json()
    provider_user_id = providers[0]["usuario_id"]

    data = client.get(f"/users/{provider_user_id}/overview", headers=auth(admin_token)).json()

    assert data["proveedor"]["id_proveedor"] == providers[0]["id_proveedor"]
    assert data["resumen"]["productos"] == len(data["productos"]) >= 1
    assert data["ordenes_pago"], "el pago de la reserva genera una orden al proveedor"
    assert Decimal(data["resumen"]["por_cobrar"]) > 0


def test_non_admin_cannot_see_overview(client, db_session):
    token, _ = create_client_with_token(client, db_session, email="curioso@example.com", identificacion="720720720")

    response = client.get(f"/users/{user_id(db_session, 'curioso@example.com')}/overview", headers=auth(token))

    assert response.status_code == 403


def test_overview_of_missing_user_returns_404(client, db_session):
    _, admin_token = create_package_ready_for_payment(client, db_session)

    assert client.get("/users/999999/overview", headers=auth(admin_token)).status_code == 404


def test_overview_of_user_without_profiles(client, db_session):
    _, admin_token = create_package_ready_for_payment(client, db_session)
    create_client_with_token(client, db_session, email="solo@example.com", identificacion="730730730")
    login_user(client, "solo@example.com")

    data = client.get(f"/users/{user_id(db_session, 'solo@example.com')}/overview", headers=auth(admin_token)).json()

    assert data["reservas"] == []
    assert data["productos"] == []
    assert data["resumen"]["total_pagado"] in ("0", "0.00", 0)

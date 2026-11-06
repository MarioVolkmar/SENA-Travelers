from datetime import date
from decimal import Decimal

from app.models.notification_email_model import NotificationEmailModel
from app.models.payment_model import PaymentModel

from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
)

# Paquete de prueba: viaje el 2026-09-10; reserva de 2 personas x 650.000 = 1.300.000
TRIP_DAY = date(2026, 9, 10)
FREE_UNTIL = date(2026, 9, 3)  # 7 días antes del viaje


def setup_reservation(client, db_session, email="cliente_cancela@example.com", identificacion="900900900", pay=True):
    package, _ = create_package_ready_for_reservation(client, db_session)
    token, _ = create_client_with_token(client, db_session, email=email, identificacion=identificacion)
    reservation = create_reservation(client, token, package["id_paquete_turistico"]).json()

    if pay:
        payment = client.post(
            "/payments/",
            json={
                "reserva_id": reservation["id_reserva"],
                "metodo_pago": "tarjeta",
                "valor": reservation["total_reserva"],
            },
            headers=headers(token),
        )
        assert payment.status_code == 201, payment.json()

    return token, reservation


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def payment_status(db_session, reserva_id):
    # MySQL (REPEATABLE READ): cerrar la transacción para ver lo que guardó la API
    db_session.rollback()
    payment = db_session.query(PaymentModel).filter(PaymentModel.reserva_id == reserva_id).first()
    return payment.estado_pago


def test_cancellation_policy_is_public(client):
    assert client.get("/reservations/cancellation-policy").json() == {
        "dias_sin_penalidad": 7,
        "porcentaje_penalidad": 30,
    }


def test_paid_reservation_cancelled_in_time_gets_full_refund(client, db_session):
    token, reservation = setup_reservation(client, db_session)
    url = f"/reservations/{reservation['id_reserva']}"

    preview = client.get(f"{url}/cancellation", headers=headers(token)).json()
    assert preview["puede_cancelar"] is True
    assert preview["con_penalidad"] is False
    assert preview["fecha_limite_sin_penalidad"] == "2026-09-03"
    assert Decimal(preview["reembolso"]) == Decimal("1300000.00")

    response = client.patch(f"{url}/cancel", headers=headers(token))

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["estado"] == "cancelada"
    assert Decimal(data["penalidad_cancelacion"]) == Decimal("0")
    assert Decimal(data["reembolso"]) == Decimal("1300000.00")
    assert data["fecha_cancelacion"] is not None
    assert payment_status(db_session, reservation["id_reserva"]) == "reembolsado"


def test_last_free_day_has_no_penalty(client, db_session, frozen_today):
    token, reservation = setup_reservation(client, db_session)
    frozen_today(FREE_UNTIL)

    data = client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=headers(token)).json()

    assert Decimal(data["penalidad_cancelacion"]) == Decimal("0")


def test_late_cancellation_charges_penalty(client, db_session, frozen_today):
    token, reservation = setup_reservation(client, db_session)
    frozen_today(date(2026, 9, 4))
    url = f"/reservations/{reservation['id_reserva']}"

    preview = client.get(f"{url}/cancellation", headers=headers(token)).json()
    assert preview["con_penalidad"] is True
    assert preview["porcentaje_penalidad"] == 30
    assert Decimal(preview["penalidad"]) == Decimal("390000.00")
    assert Decimal(preview["reembolso"]) == Decimal("910000.00")

    data = client.patch(f"{url}/cancel", headers=headers(token)).json()

    assert Decimal(data["penalidad_cancelacion"]) == Decimal("390000.00")
    assert Decimal(data["reembolso"]) == Decimal("910000.00")
    assert payment_status(db_session, reservation["id_reserva"]) == "reembolso_parcial"


def test_unpaid_reservation_has_no_penalty_even_if_late(client, db_session, frozen_today):
    token, reservation = setup_reservation(client, db_session, pay=False)
    frozen_today(date(2026, 9, 8))

    data = client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=headers(token)).json()

    assert data["estado"] == "cancelada"
    assert Decimal(data["penalidad_cancelacion"]) == Decimal("0")
    assert Decimal(data["reembolso"]) == Decimal("0")


def test_cannot_cancel_on_trip_day(client, db_session, frozen_today):
    token, reservation = setup_reservation(client, db_session)
    frozen_today(TRIP_DAY)
    url = f"/reservations/{reservation['id_reserva']}"

    preview = client.get(f"{url}/cancellation", headers=headers(token)).json()
    assert preview["puede_cancelar"] is False

    response = client.patch(f"{url}/cancel", headers=headers(token))
    assert response.status_code == 400
    assert "fecha del viaje" in response.json()["detail"]


def test_cancellation_sends_email_notification(client, db_session, frozen_today):
    token, reservation = setup_reservation(client, db_session)
    frozen_today(date(2026, 9, 5))

    client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=headers(token))

    db_session.rollback()
    notification = (
        db_session.query(NotificationEmailModel)
        .filter(
            NotificationEmailModel.reservas_id_reserva == reservation["id_reserva"],
            NotificationEmailModel.tipo_notificacion == "cancelacion_reserva",
        )
        .first()
    )

    assert notification is not None
    assert "penalidad" in notification.mensaje


def test_other_client_cannot_preview_or_cancel(client, db_session):
    _, reservation = setup_reservation(client, db_session)
    other_token, _ = create_client_with_token(
        client, db_session, email="otro_cancela@example.com", identificacion="910910910"
    )
    url = f"/reservations/{reservation['id_reserva']}"

    assert client.get(f"{url}/cancellation", headers=headers(other_token)).status_code == 403
    assert client.patch(f"{url}/cancel", headers=headers(other_token)).status_code == 403


def test_cancelled_reservation_cannot_be_paid(client, db_session):
    token, reservation = setup_reservation(client, db_session, pay=False)
    client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=headers(token))

    payment = client.post(
        "/payments/",
        json={
            "reserva_id": reservation["id_reserva"],
            "metodo_pago": "tarjeta",
            "valor": reservation["total_reserva"],
        },
        headers=headers(token),
    )

    assert payment.status_code == 400

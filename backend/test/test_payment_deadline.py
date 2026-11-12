"""
Límites en un solo lugar (GET /config/limits) y vencimiento de las reservas pendientes
que no se pagan a tiempo (se cancelan solas y liberan sus cupos).
"""
from datetime import datetime, timedelta

from app.core.constants import (
    LIMITS,
    RESERVATION_STATUS_CANCELLED,
    RESERVATION_STATUS_CONFIRMED,
    RESERVATION_STATUS_PENDING,
)
from app.models.payment_model import PaymentModel
from app.models.reservation_model import ReservationModel
from app.services.reservation_service import ReservationService
from app.services.stripe_service import StripeService

from test_stripe import fresh, pending_reservation, session_for, signed_webhook, stripe_keys  # noqa: F401
from test_reservations import create_admin_with_token, create_reservation


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def make_overdue(db_session, reserva_id, hours=25):
    """Simula que la reserva se creó hace `hours` horas."""
    db = fresh(db_session)
    reservation = db.query(ReservationModel).filter(ReservationModel.id_reserva == reserva_id).one()
    reservation.fecha_compra = datetime.now() - timedelta(hours=hours)
    db.commit()


def reservation_row(db_session, reserva_id):
    return fresh(db_session).query(ReservationModel).filter(ReservationModel.id_reserva == reserva_id).one()


# ------------------------------------------------------------------ límites

def test_limits_endpoint_returns_backend_limits(client):
    response = client.get("/config/limits")

    assert response.status_code == 200
    data = response.json()
    assert data["limites"] == LIMITS
    assert data["limites"]["reservationTravelers"] == {"min": 1, "max": 10}
    assert data["limites"]["paymentHours"] == {"min": 1, "max": 168}
    assert data["iva_porcentaje"] == 19


def test_payment_hours_setting_uses_its_range(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)

    assert client.patch("/settings/", json={"horas_para_pagar": 0}, headers=auth(admin_token)).status_code == 422
    assert client.patch("/settings/", json={"horas_para_pagar": 169}, headers=auth(admin_token)).status_code == 422

    updated = client.patch("/settings/", json={"horas_para_pagar": 48}, headers=auth(admin_token))
    assert updated.status_code == 200
    assert updated.json()["horas_para_pagar"] == 48
    assert client.get("/reservations/cancellation-policy").json()["horas_para_pagar"] == 48


# ------------------------------------------------------------------ plazo para pagar

def test_pending_reservation_shows_payment_deadline(client, db_session):
    token, reservation = pending_reservation(client, db_session)

    deadline = datetime.fromisoformat(reservation["vence_pago"])
    assert deadline.tzinfo is not None  # con zona horaria: el navegador la muestra en la hora local
    row = reservation_row(db_session, reservation["id_reserva"])
    expected = (row.fecha_compra + timedelta(hours=24)).astimezone()
    assert abs((deadline - expected).total_seconds()) < 2

    mine = client.get("/reservations/me", headers=auth(token)).json()
    assert mine[0]["vence_pago"] is not None


def test_overdue_reservations_expire_and_free_their_slots(client, db_session):
    token, overdue = pending_reservation(client, db_session)
    recent = create_reservation(client, token, package_id=overdue["id_paquete_turistico"]).json()
    make_overdue(db_session, overdue["id_reserva"])

    before = client.get(f"/reservations/availability/{overdue['id_paquete_turistico']}").json()["cupos_disponibles"]
    expired = ReservationService(fresh(db_session)).expire_unpaid_reservations()

    assert expired == 1
    row = reservation_row(db_session, overdue["id_reserva"])
    assert row.estado == RESERVATION_STATUS_CANCELLED
    assert row.penalidad_cancelacion is None and row.reembolso is None
    assert ReservationService.is_expired_cancellation(row)
    assert reservation_row(db_session, recent["id_reserva"]).estado == RESERVATION_STATUS_PENDING

    after = client.get(f"/reservations/availability/{overdue['id_paquete_turistico']}").json()["cupos_disponibles"]
    assert after == before + overdue["cantidad_personas"]

    # Ya cancelada: una segunda pasada no hace nada
    assert ReservationService(fresh(db_session)).expire_unpaid_reservations() == 0


def test_cannot_start_payment_after_deadline(client, db_session):
    token, reservation = pending_reservation(client, db_session)
    make_overdue(db_session, reservation["id_reserva"])

    simulated = client.post(
        "/payments/",
        json={"reserva_id": reservation["id_reserva"], "metodo_pago": "Nequi", "valor": reservation["total_reserva"]},
        headers=auth(token),
    )
    assert simulated.status_code == 400
    assert "venció" in simulated.json()["detail"]

    checkout = client.post(
        "/payments/stripe/checkout", json={"reserva_id": reservation["id_reserva"]}, headers=auth(token)
    )
    assert checkout.status_code == 400
    assert "venció" in checkout.json()["detail"]


def test_late_stripe_payment_reactivates_expired_reservation(client, db_session):
    _, reservation = pending_reservation(client, db_session)
    make_overdue(db_session, reservation["id_reserva"])
    ReservationService(fresh(db_session)).expire_unpaid_reservations()

    response = signed_webhook(client, session_for(reservation))

    assert response.status_code == 200, response.json()
    row = reservation_row(db_session, reservation["id_reserva"])
    assert row.estado == RESERVATION_STATUS_CONFIRMED
    assert row.fecha_cancelacion is None
    assert fresh(db_session).query(PaymentModel).filter(PaymentModel.reserva_id == reservation["id_reserva"]).count() == 1


def test_late_stripe_payment_is_refunded_when_reservation_was_cancelled_by_traveler(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=auth(token))

    calls = []

    def fake_request(self, method, path, data=None):
        calls.append((method, path, data))
        return {"id": "re_test_1", "status": "succeeded"}

    monkeypatch.setattr(StripeService, "_request", fake_request)
    session = session_for(reservation)

    try:
        StripeService(fresh(db_session)).process_session(session)
        raise AssertionError("Debió rechazar el pago")
    except ValueError as error:
        assert "devolvimos el pago" in str(error)

    assert calls and calls[0][1] == "/refunds"
    assert calls[0][2]["payment_intent"] == "pi_test_123"
    assert reservation_row(db_session, reservation["id_reserva"]).estado == RESERVATION_STATUS_CANCELLED
    assert fresh(db_session).query(PaymentModel).filter(PaymentModel.reserva_id == reservation["id_reserva"]).count() == 0


# ------------------------------------------------------------------ aviso antes de vencer

def test_payment_reminder_lead_is_four_hours_or_half_the_term():
    assert ReservationService.payment_reminder_lead(24) == 4
    assert ReservationService.payment_reminder_lead(8) == 4
    assert ReservationService.payment_reminder_lead(2) == 1


def test_unpaid_reservation_gets_one_reminder_before_expiring(client, db_session):
    token, reservation = pending_reservation(client, db_session)
    reserva_id = reservation["id_reserva"]

    # Recién creada (plazo de 24 h): todavía no se avisa
    assert ReservationService(fresh(db_session)).remind_unpaid_reservations() == 0

    # Faltan 3 horas: se avisa una sola vez
    make_overdue(db_session, reserva_id, hours=21)
    assert ReservationService(fresh(db_session)).remind_unpaid_reservations() == 1
    assert ReservationService(fresh(db_session)).remind_unpaid_reservations() == 0
    assert reservation_row(db_session, reserva_id).recordatorio_pago is not None
    assert reservation_row(db_session, reserva_id).estado == RESERVATION_STATUS_PENDING

    items = client.get("/notifications/app", headers=auth(token)).json()["notificaciones"]
    reminder = next(item for item in items if item["tipo"] == "recordatorio_pago")
    assert "por vencer" in reminder["titulo"]
    assert "2 horas" in reminder["mensaje"] or "3 horas" in reminder["mensaje"]


def test_expired_or_paid_reservations_are_not_reminded(client, db_session):
    token, expired = pending_reservation(client, db_session)
    make_overdue(db_session, expired["id_reserva"], hours=25)  # ya venció: se cancela, no se avisa

    assert ReservationService(fresh(db_session)).remind_unpaid_reservations() == 0
    assert reservation_row(db_session, expired["id_reserva"]).recordatorio_pago is None

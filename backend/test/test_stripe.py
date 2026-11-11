"""
Pagos con Stripe. No se llama al API real: las llamadas a Stripe se reemplazan con monkeypatch.
"""
import hashlib
import hmac
import json
import time

import pytest

from app.core.constants import RESERVATION_STATUS_CONFIRMED, RESERVATION_STATUS_PENDING
from app.models.payment_model import PaymentModel
from app.models.provider_payment_order_model import ProviderPaymentOrderModel
from app.models.reservation_model import ReservationModel
from app.services import stripe_service
from app.services.stripe_service import StripeService

from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
)

WEBHOOK_SECRET = "whsec_secretoDePrueba"


@pytest.fixture(autouse=True)
def stripe_keys(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_llaveDePrueba")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("FRONTEND_URL", "https://travelers.test")


def fresh(db_session):
    db_session.rollback()
    db_session.expire_all()
    return db_session


def pending_reservation(client, db_session, email="viajero_stripe@example.com", identificacion="888000111"):
    package, _ = create_package_ready_for_reservation(client, db_session)
    token, _ = create_client_with_token(client, db_session, email=email, identificacion=identificacion)
    response = create_reservation(client, token, package_id=package["id_paquete_turistico"])
    assert response.status_code == 201, response.json()
    return token, response.json()


def session_for(reservation, payment_status="paid", **changes):
    data = {
        "id": "cs_test_a1b2c3",
        "object": "checkout.session",
        "payment_status": payment_status,
        "currency": "cop",
        "amount_total": int(float(reservation["total_reserva"]) * 100),
        "client_reference_id": reservation["codigo_reserva"],
        "metadata": {"codigo_reserva": reservation["codigo_reserva"]},
        "payment_intent": {"id": "pi_test_123", "payment_method": {"type": "card"}},
        "livemode": False,
    }
    data.update(changes)
    return data


def signed_webhook(client, session, secret=WEBHOOK_SECRET, timestamp=None, event_type="checkout.session.completed"):
    payload = json.dumps({"id": "evt_test", "type": event_type, "data": {"object": session}}).encode()
    timestamp = timestamp or int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    return client.post(
        "/payments/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": f"t={timestamp},v1={signature}", "Content-Type": "application/json"},
    )


def payments_of(db_session, reserva_id):
    return fresh(db_session).query(PaymentModel).filter(PaymentModel.reserva_id == reserva_id).all()


def reservation_status(db_session, reserva_id):
    return fresh(db_session).query(ReservationModel).filter(ReservationModel.id_reserva == reserva_id).one().estado


# ------------------------------------------------------------------ configuración y checkout

def test_config(client, monkeypatch):
    assert client.get("/payments/stripe/config").json() == {"enabled": True, "test_mode": True}
    monkeypatch.delenv("STRIPE_SECRET_KEY")
    assert client.get("/payments/stripe/config").json()["enabled"] is False


def test_checkout_creates_session_with_reservation_amount(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    sent = {}

    def fake_request(self, method, path, data=None):
        sent.update(method=method, path=path, data=data)
        return {"id": "cs_test_nueva", "url": "https://checkout.stripe.com/c/pay/cs_test_nueva", "livemode": False}

    monkeypatch.setattr(StripeService, "_request", fake_request)
    response = client.post(
        "/payments/stripe/checkout",
        json={"reserva_id": reservation["id_reserva"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.json()
    assert response.json()["checkout_url"].startswith("https://checkout.stripe.com/")
    assert sent["path"] == "/checkout/sessions"
    assert sent["data"]["line_items[0][price_data][currency]"] == "cop"
    assert sent["data"]["line_items[0][price_data][unit_amount]"] == int(float(reservation["total_reserva"]) * 100)
    assert sent["data"]["metadata[codigo_reserva]"] == reservation["codigo_reserva"]
    assert sent["data"]["success_url"] == "https://travelers.test/reservations?stripe_session={CHECKOUT_SESSION_ID}"


def test_cannot_checkout_someone_elses_reservation(client, db_session):
    _, reservation = pending_reservation(client, db_session)
    other_token, _ = create_client_with_token(client, db_session, email="otro_stripe@example.com", identificacion="888000222")

    response = client.post(
        "/payments/stripe/checkout",
        json={"reserva_id": reservation["id_reserva"]},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


# ------------------------------------------------------------------ confirmación al volver

def test_confirm_paid_session_confirms_reservation(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    monkeypatch.setattr(StripeService, "fetch_session", lambda self, sid: session_for(reservation))

    response = client.post(
        "/payments/stripe/confirm",
        json={"session_id": "cs_test_a1b2c3"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.json()
    assert response.json()["status"] == "paid"
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_CONFIRMED
    payments = payments_of(db_session, reservation["id_reserva"])
    assert len(payments) == 1
    assert payments[0].metodo_pago == "Stripe · Tarjeta"
    assert payments[0].referencia_pago == "pi_test_123"
    assert fresh(db_session).query(ProviderPaymentOrderModel).filter(
        ProviderPaymentOrderModel.reserva_id == reservation["id_reserva"]
    ).count() >= 1


def test_confirm_unpaid_session_keeps_reservation_pending(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    monkeypatch.setattr(StripeService, "fetch_session", lambda self, sid: session_for(reservation, payment_status="unpaid"))

    response = client.post(
        "/payments/stripe/confirm",
        json={"session_id": "cs_test_a1b2c3"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "unpaid"
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_PENDING
    assert payments_of(db_session, reservation["id_reserva"]) == []


def test_confirm_rejects_amount_mismatch(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    monkeypatch.setattr(StripeService, "fetch_session", lambda self, sid: session_for(reservation, amount_total=100))

    response = client.post(
        "/payments/stripe/confirm",
        json={"session_id": "cs_test_a1b2c3"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_PENDING


def test_cannot_confirm_session_of_another_traveler(client, db_session, monkeypatch):
    _, reservation = pending_reservation(client, db_session)
    other_token, _ = create_client_with_token(client, db_session, email="ajeno_stripe@example.com", identificacion="888000333")
    monkeypatch.setattr(StripeService, "fetch_session", lambda self, sid: session_for(reservation))

    response = client.post(
        "/payments/stripe/confirm",
        json={"session_id": "cs_test_a1b2c3"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403
    assert payments_of(db_session, reservation["id_reserva"]) == []


# ------------------------------------------------------------------ webhook

def test_signed_webhook_confirms_reservation(client, db_session):
    _, reservation = pending_reservation(client, db_session)

    response = signed_webhook(client, session_for(reservation))

    assert response.status_code == 200, response.json()
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_CONFIRMED


def test_webhook_with_wrong_secret_is_rejected(client, db_session):
    _, reservation = pending_reservation(client, db_session)

    response = signed_webhook(client, session_for(reservation), secret="whsec_otroSecreto")

    assert response.status_code == 400
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_PENDING


def test_webhook_with_old_signature_is_rejected(client, db_session):
    _, reservation = pending_reservation(client, db_session)

    response = signed_webhook(client, session_for(reservation), timestamp=int(time.time()) - 3600)

    assert response.status_code == 400


def test_webhook_and_return_do_not_register_payment_twice(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    session = session_for(reservation)

    assert signed_webhook(client, session).status_code == 200
    monkeypatch.setattr(StripeService, "fetch_session", lambda self, sid: session)
    response = client.post(
        "/payments/stripe/confirm",
        json={"session_id": session["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(payments_of(db_session, reservation["id_reserva"])) == 1


def test_other_event_types_are_ignored(client, db_session):
    _, reservation = pending_reservation(client, db_session)

    response = signed_webhook(client, session_for(reservation), event_type="customer.created")

    assert response.status_code == 200
    assert response.json() == {"ignored": True}
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_PENDING


# ------------------------------------------------------------------ reembolsos al cancelar

def paid_with_stripe(client, db_session, monkeypatch, **reservation_kwargs):
    token, reservation = pending_reservation(client, db_session, **reservation_kwargs)
    monkeypatch.setattr(StripeService, "fetch_session", lambda self, sid: session_for(reservation))
    response = client.post(
        "/payments/stripe/confirm",
        json={"session_id": "cs_test_a1b2c3"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.json()
    return token, reservation


def capture_refunds(monkeypatch, fail=False):
    calls = []

    def fake_request(self, method, path, data=None):
        assert path == "/refunds"
        if fail:
            import requests
            raise requests.HTTPError("Stripe caído")
        calls.append(data)
        return {"id": "re_test_1", "status": "succeeded"}

    monkeypatch.setattr(StripeService, "_request", fake_request)
    return calls


def test_cancelling_stripe_payment_refunds_full_amount_in_stripe(client, db_session, monkeypatch):
    token, reservation = paid_with_stripe(client, db_session, monkeypatch)
    calls = capture_refunds(monkeypatch)

    # 1 de agosto: el viaje es el 10 de septiembre, dentro del plazo sin penalidad
    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.json()
    assert len(calls) == 1
    assert calls[0]["payment_intent"] == "pi_test_123"
    assert calls[0]["amount"] == int(float(reservation["total_reserva"]) * 100)
    assert reservation_status(db_session, reservation["id_reserva"]) == "cancelada"


def test_late_cancellation_refunds_only_the_amount_after_penalty(client, db_session, monkeypatch, frozen_today):
    from datetime import date

    token, reservation = paid_with_stripe(client, db_session, monkeypatch)
    calls = capture_refunds(monkeypatch)
    frozen_today(date(2026, 9, 7))  # 3 días antes del viaje: aplica la penalidad

    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.json()
    total = int(float(reservation["total_reserva"]) * 100)
    assert 0 < calls[0]["amount"] < total
    assert calls[0]["amount"] == int(float(response.json()["reembolso"]) * 100)


def test_if_stripe_refund_fails_the_reservation_is_not_cancelled(client, db_session, monkeypatch):
    token, reservation = paid_with_stripe(client, db_session, monkeypatch)
    capture_refunds(monkeypatch, fail=True)

    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "reembolso" in response.json()["detail"]
    assert reservation_status(db_session, reservation["id_reserva"]) == RESERVATION_STATUS_CONFIRMED
    assert payments_of(db_session, reservation["id_reserva"])[0].estado_pago == "aprobado"


def test_simulated_payments_do_not_call_stripe(client, db_session, monkeypatch):
    token, reservation = pending_reservation(client, db_session)
    paid = client.post(
        "/payments/",
        json={"reserva_id": reservation["id_reserva"], "metodo_pago": "Nequi", "valor": reservation["total_reserva"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert paid.status_code == 201, paid.json()
    calls = capture_refunds(monkeypatch)

    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert calls == []


def test_amount_helper():
    assert stripe_service.amount_in_cents("1250000.00") == 125000000

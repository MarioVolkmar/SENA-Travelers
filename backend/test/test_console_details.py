"""
Fichas de la consola y nuevas reglas de pagos a proveedores:
datos bancarios obligatorios, día de pago programado, comprobante, aviso de plazo,
paquetes que usan un producto y la ficha completa de una reserva.
"""
from datetime import date, timedelta

from app.core import clock
from app.models.provider_payment_order_model import ProviderPaymentOrderModel
from app.services import provider_payment_order_service as order_module
from app.services.provider_payment_order_service import ProviderPaymentOrderService, next_payment_date

from test_provider_payments import auth, book_and_pay, setup

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def first_order(client, admin_token):
    return client.get("/provider-payments/", headers=auth(admin_token)).json()[0]


# ------------------------------------------------------------------ datos bancarios

def test_order_cannot_be_approved_or_paid_without_bank_data(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session, with_bank=False)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order = first_order(client, admin_token)
    assert order["tiene_datos_bancarios"] is False

    approve = client.patch(f"/provider-payments/{order['id_orden']}/approve", headers=auth(admin_token))
    pay = client.patch(f"/provider-payments/{order['id_orden']}/pay", json={"referencia_pago": "TRF-1"}, headers=auth(admin_token))

    assert approve.status_code == 400
    assert "datos bancarios" in approve.json()["detail"]
    assert pay.status_code == 400
    assert "datos bancarios" in pay.json()["detail"]


# ------------------------------------------------------------------ día de pago

def test_next_payment_date_uses_configured_day():
    assert next_payment_date(15, date(2026, 11, 10)) == date(2026, 11, 15)
    assert next_payment_date(15, date(2026, 11, 15)) == date(2026, 11, 15)
    assert next_payment_date(15, date(2026, 11, 16)) == date(2026, 12, 15)
    assert next_payment_date(5, date(2026, 12, 20)) == date(2027, 1, 5)


def test_approved_order_shows_scheduled_payment_date(client, db_session, monkeypatch):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    client.patch("/settings/", json={"dia_pago_proveedores": 10}, headers=auth(admin_token))
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    # El cálculo de la fecha de pago se hace con "hoy" = 20 de noviembre
    monkeypatch.setattr(clock, "today", lambda: date(2026, 11, 20))
    order = first_order(client, admin_token)
    assert order["fecha_pago_programada"] is None  # pendiente: aún no tiene fecha de pago

    approved = client.patch(f"/provider-payments/{order['id_orden']}/approve", headers=auth(admin_token)).json()
    assert approved["fecha_pago_programada"] == "2026-12-10"

    schedule = client.get("/provider-payments/schedule", headers=auth(provider_token)).json()
    assert schedule == {"dia_pago": 10, "proximo_pago": "2026-12-10", "dias_para_aprobar": 15}
    assert client.patch("/settings/", json={"dia_pago_proveedores": 29}, headers=auth(admin_token)).status_code == 422


# ------------------------------------------------------------------ comprobante

def test_receipt_image_is_attached_to_paid_order(client, db_session, monkeypatch):
    uploaded = []
    monkeypatch.setattr(order_module.storage, "upload_file", lambda key, data, content_type: uploaded.append((key, content_type)))
    monkeypatch.setattr(order_module.storage, "public_url", lambda key: f"https://cdn.test/{key}")
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order = first_order(client, admin_token)
    url = f"/provider-payments/{order['id_orden']}/receipt"

    # Antes de pagarla no se puede adjuntar
    early = client.post(url, files={"file": ("pago.png", PNG, "image/png")}, headers=auth(admin_token))
    assert early.status_code == 400

    client.patch(f"/provider-payments/{order['id_orden']}/pay", json={"referencia_pago": "TRF-77"}, headers=auth(admin_token))
    bad = client.post(url, files={"file": ("pago.txt", b"hola", "text/plain")}, headers=auth(admin_token))
    good = client.post(url, files={"file": ("pago.png", PNG, "image/png")}, headers=auth(admin_token))

    assert bad.status_code == 400
    assert good.status_code == 200, good.json()
    assert good.json()["comprobante_url"].startswith("https://cdn.test/comprobantes/")
    assert uploaded and uploaded[-1][1] == "image/png"


# ------------------------------------------------------------------ aviso de plazo

def test_admins_are_reminded_two_days_before_approval_deadline(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order_id = first_order(client, admin_token)["id_orden"]

    db_session.rollback()
    order = db_session.query(ProviderPaymentOrderModel).filter(ProviderPaymentOrderModel.id_orden == order_id).one()
    order.fecha_vencimiento = clock.today() + timedelta(days=5)
    db_session.commit()
    assert ProviderPaymentOrderService(db_session).remind_due_approvals() == 0

    order.fecha_vencimiento = clock.today() + timedelta(days=2)
    db_session.commit()
    assert ProviderPaymentOrderService(db_session).remind_due_approvals() == 1
    assert ProviderPaymentOrderService(db_session).remind_due_approvals() == 0  # una sola vez

    items = client.get("/notifications/app", headers=auth(admin_token)).json()["notificaciones"]
    assert any("por aprobar" in item["titulo"] for item in items)


# ------------------------------------------------------------------ fichas

def test_product_sheet_lists_packages_that_use_it(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    detail = client.get(f"/packages/admin/{package['id_paquete_turistico']}", headers=auth(admin_token)).json()
    product_id = detail["productos"][0]["producto_id"]

    response = client.get(f"/products/admin/{product_id}/packages", headers=auth(admin_token))

    assert response.status_code == 200
    assert response.json()[0]["id_paquete_turistico"] == package["id_paquete_turistico"]
    assert response.json()[0]["cantidad"] >= 1
    assert client.get(f"/products/admin/{product_id}/packages", headers=auth(client_token)).status_code == 403


def test_reservation_sheet_has_traveler_payment_and_orders(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])

    response = client.get(f"/reservations/{reservation['id_reserva']}/detail", headers=auth(admin_token))

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["reserva"]["codigo_reserva"] == reservation["codigo_reserva"]
    assert data["viajero"]["email"] == "viajero_op@example.com"
    assert data["pago"]["estado_pago"] == "aprobado"
    assert float(data["reserva"]["subtotal_sin_iva"]) + float(data["reserva"]["iva"]) == float(data["reserva"]["total_reserva"])
    assert len(data["ordenes"]) == 1
    assert client.get(f"/reservations/{reservation['id_reserva']}/detail", headers=auth(client_token)).status_code == 403

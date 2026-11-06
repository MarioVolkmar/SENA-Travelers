"""Reseñas, favoritos, cupones, voucher, recordatorios, notificaciones, bitácora y reportes."""
from datetime import date
from decimal import Decimal

import pytest

from app.models.notification_email_model import NotificationEmailModel
from app.models.reservation_model import ReservationModel

from test_provider_payments import auth, book_and_pay, setup

# Paquete del helper: precio 650.000 por persona, viaje 2026-09-10 → 2026-09-12. Hoy (fijo): 2026-08-01.


def coupon_payload(**overrides):
    data = {
        "codigo": "verano10",
        "descripcion": "10 % de descuento",
        "tipo": "porcentaje",
        "valor": "10",
        "fecha_inicio": "2026-07-01",
        "fecha_fin": "2026-12-31",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------
# Cupones
# ---------------------------------------------------------------

def test_coupon_discount_applies_to_reservation(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    created = client.post("/coupons/", json=coupon_payload(usos_maximos=1), headers=auth(admin_token))
    assert created.status_code == 201, created.json()
    assert created.json()["codigo"] == "VERANO10"

    preview = client.post(
        "/coupons/validate",
        json={"codigo": "Verano10", "id_paquete_turistico": package["id_paquete_turistico"], "cantidad_personas": 2},
        headers=auth(client_token),
    )
    assert preview.status_code == 200, preview.json()
    assert Decimal(preview.json()["descuento"]) == Decimal("130000")
    assert Decimal(preview.json()["total"]) == Decimal("1170000")

    response = client.post(
        "/reservations/",
        json={
            "id_paquete_turistico": package["id_paquete_turistico"],
            "fecha_reserva": "2026-09-10",
            "cantidad_personas": 1,
            "acompanantes": [],
            "codigo_cupon": "verano10",
        },
        headers=auth(client_token),
    )
    assert response.status_code == 201, response.json()
    assert Decimal(response.json()["total_reserva"]) == Decimal("585000")
    assert Decimal(response.json()["descuento_cupon"]) == Decimal("65000")

    # Con un solo uso permitido, el segundo intento ya no aplica
    again = client.post(
        "/coupons/validate",
        json={"codigo": "VERANO10", "id_paquete_turistico": package["id_paquete_turistico"], "cantidad_personas": 1},
        headers=auth(client_token),
    )
    assert again.status_code == 400
    assert "límite" in again.json()["detail"]

    # Usado en una reserva: no se elimina, se desactiva
    coupon_id = created.json()["id_cupon"]
    assert client.delete(f"/coupons/{coupon_id}", headers=auth(admin_token)).status_code == 409


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"fecha_fin": "2026-07-15"}, "venció"),
        ({"fecha_inicio": "2026-08-10"}, "vigente"),
        ({"estado": "inactivo"}, "activo"),
        ({"monto_minimo": "5000000"}, "desde"),
    ],
)
def test_invalid_coupons_are_rejected(client, db_session, overrides, message):
    package, admin_token, client_token, _ = setup(client, db_session)
    client.post("/coupons/", json=coupon_payload(**overrides), headers=auth(admin_token))

    response = client.post(
        "/coupons/validate",
        json={"codigo": "VERANO10", "id_paquete_turistico": package["id_paquete_turistico"], "cantidad_personas": 1},
        headers=auth(client_token),
    )
    assert response.status_code == 400
    assert message in response.json()["detail"]


def test_fixed_amount_coupon_never_exceeds_total(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    client.post("/coupons/", json=coupon_payload(codigo="GRATIS", tipo="valor", valor="9000000"), headers=auth(admin_token))

    preview = client.post(
        "/coupons/validate",
        json={"codigo": "gratis", "id_paquete_turistico": package["id_paquete_turistico"], "cantidad_personas": 1},
        headers=auth(client_token),
    ).json()
    assert Decimal(preview["total"]) == 0


def test_only_admins_manage_coupons(client, db_session):
    _, _, client_token, _ = setup(client, db_session)
    assert client.post("/coupons/", json=coupon_payload(), headers=auth(client_token)).status_code == 403
    assert client.get("/coupons/", headers=auth(client_token)).status_code == 403


# ---------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------

def test_favorites_add_list_and_remove(client, db_session):
    package, _, client_token, _ = setup(client, db_session)
    package_id = package["id_paquete_turistico"]

    assert client.post(f"/favorites/{package_id}", headers=auth(client_token)).json() == [package_id]
    assert client.post(f"/favorites/{package_id}", headers=auth(client_token)).json() == [package_id]  # sin duplicar
    assert [p["id_paquete_turistico"] for p in client.get("/favorites/", headers=auth(client_token)).json()] == [package_id]
    assert client.delete(f"/favorites/{package_id}", headers=auth(client_token)).json() == []
    assert client.post("/favorites/99999", headers=auth(client_token)).status_code == 404


# ---------------------------------------------------------------
# Reseñas
# ---------------------------------------------------------------

def test_review_only_after_trip_and_once(client, db_session, frozen_today):
    package, admin_token, client_token, _ = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])
    payload = {"reserva_id": reservation["id_reserva"], "calificacion": 5, "comentario": "¡Increíble!"}

    early = client.post("/reviews/", json=payload, headers=auth(client_token))
    assert early.status_code == 400
    assert client.get("/reviews/me/pending", headers=auth(client_token)).json() == []

    frozen_today(date(2026, 9, 15))
    pending = client.get("/reviews/me/pending", headers=auth(client_token)).json()
    assert [item["reserva_id"] for item in pending] == [reservation["id_reserva"]]

    created = client.post("/reviews/", json=payload, headers=auth(client_token))
    assert created.status_code == 201, created.json()
    assert created.json()["autor"].endswith(".") or " " not in created.json()["autor"]

    assert client.post("/reviews/", json=payload, headers=auth(client_token)).status_code == 400

    public = client.get(f"/reviews/package/{package['id_paquete_turistico']}").json()
    assert public["total"] == 1 and public["promedio"] == 5
    assert client.get("/reviews/summary").json() == [
        {"paquete_id": package["id_paquete_turistico"], "promedio": 5.0, "total": 1}
    ]

    # El administrador puede ocultarla
    review_id = created.json()["id_resena"]
    hidden = client.patch(f"/reviews/{review_id}/status", json={"estado": "oculta"}, headers=auth(admin_token))
    assert hidden.status_code == 200
    assert client.get(f"/reviews/package/{package['id_paquete_turistico']}").json()["total"] == 0


def test_cannot_review_someone_elses_trip(client, db_session, frozen_today):
    from test_reservations import create_client_with_token

    package, _, client_token, _ = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])
    other_token, _ = create_client_with_token(client, db_session, email="otro_res@example.com", identificacion="811811811")
    frozen_today(date(2026, 9, 15))

    response = client.post(
        "/reviews/", json={"reserva_id": reservation["id_reserva"], "calificacion": 1}, headers=auth(other_token)
    )
    assert response.status_code == 403


# ---------------------------------------------------------------
# Voucher con QR
# ---------------------------------------------------------------

def test_voucher_pdf_and_public_verification(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    pending = book_and_pay(client, client_token, package["id_paquete_turistico"], pay=False)
    assert client.get(f"/vouchers/{pending['id_reserva']}", headers=auth(client_token)).status_code == 400

    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])
    response = client.get(f"/vouchers/{reservation['id_reserva']}", headers=auth(client_token))
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")

    verification = client.get(f"/vouchers/verify/{reservation['codigo_reserva'].lower()}").json()
    assert verification["valida"] is True
    assert verification["codigo_reserva"] == reservation["codigo_reserva"]
    assert client.get("/vouchers/verify/RES-NOEXISTE").status_code == 404


# ---------------------------------------------------------------
# Recordatorios
# ---------------------------------------------------------------

def test_trip_reminder_sent_once_inside_window(client, db_session, frozen_today):
    package, admin_token, client_token, _ = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])

    assert client.post("/reminders/run", headers=auth(admin_token)).json() == {"enviados": 0}  # faltan 40 días

    frozen_today(date(2026, 9, 8))  # faltan 2 días (ventana de 3)
    assert client.post("/reminders/run", headers=auth(admin_token)).json() == {"enviados": 1}
    assert client.post("/reminders/run", headers=auth(admin_token)).json() == {"enviados": 0}  # no repite

    db_session.rollback()
    email = (
        db_session.query(NotificationEmailModel)
        .filter(NotificationEmailModel.tipo_notificacion == "recordatorio_viaje")
        .one()
    )
    assert email.reservas_id_reserva == reservation["id_reserva"]
    assert db_session.get(ReservationModel, reservation["id_reserva"]).recordatorio_enviado is not None

    bell = client.get("/notifications/app", headers=auth(client_token)).json()
    assert any(item["tipo"] == "recordatorio_viaje" for item in bell["notificaciones"])
    assert client.post("/reminders/run", headers=auth(client_token)).status_code == 403


# ---------------------------------------------------------------
# Notificaciones en la app
# ---------------------------------------------------------------

def test_bell_notifications_and_mark_read(client, db_session):
    package, _, client_token, provider_token = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])

    bell = client.get("/notifications/app", headers=auth(client_token)).json()
    tipos = [item["tipo"] for item in bell["notificaciones"]]
    assert "reserva_creada" in tipos and "pago_aprobado" in tipos
    assert bell["no_leidas"] == len(tipos)

    first = bell["notificaciones"][0]["id_notificacion"]
    assert client.patch(f"/notifications/app/{first}/read", headers=auth(client_token)).json()["leida"] is True
    assert client.patch(f"/notifications/app/{first}/read", headers=auth(provider_token)).status_code == 403
    assert client.patch("/notifications/app/read-all", headers=auth(client_token)).json()["no_leidas"] == 0

    # El proveedor recibió aviso de su nueva orden de pago
    provider_bell = client.get("/notifications/app", headers=auth(provider_token)).json()
    assert any(item["tipo"] == "orden_pago" for item in provider_bell["notificaciones"])


# ---------------------------------------------------------------
# Bitácora de administradores
# ---------------------------------------------------------------

def test_admin_actions_are_logged(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"], pay=False)

    client.patch(f"/reservations/{reservation['id_reserva']}/status", json={"estado": "cancelada"}, headers=auth(admin_token))
    client.post("/coupons/", json=coupon_payload(), headers=auth(admin_token))
    client.patch("/settings/", json={"dias_recordatorio_viaje": 5}, headers=auth(admin_token))
    # Un intento fallido no se registra
    client.patch(f"/reservations/{reservation['id_reserva']}/status", json={"estado": "confirmada"}, headers=auth(admin_token))

    entries = client.get("/audit/", headers=auth(admin_token)).json()
    descriptions = [entry["descripcion"] for entry in entries]

    assert f"Cambió el estado de la reserva #{reservation['id_reserva']} a cancelada" in descriptions
    assert "Creó el cupón VERANO10" in descriptions
    assert any("dias_recordatorio_viaje=5" in text for text in descriptions)
    assert not any("a confirmada" in text for text in descriptions)
    # La creación del paquete del helper también quedó
    assert any(text.startswith("Creó el paquete") for text in descriptions)

    filtered = client.get("/audit/?entidad=cupon", headers=auth(admin_token)).json()
    assert [entry["entidad"] for entry in filtered] == ["cupon"]
    assert client.get("/audit/", headers=auth(client_token)).status_code == 403


# ---------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------

def test_reports_summary_and_exports(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    book_and_pay(client, client_token, package["id_paquete_turistico"], people=1, pay=False)

    summary = client.get("/reports/summary?desde=2025-06-01&hasta=2027-12-31", headers=auth(admin_token))
    assert summary.status_code == 200, summary.json()
    data = summary.json()
    assert data["kpis"]["reservas"] == 2
    assert Decimal(data["kpis"]["ventas_netas"]) == Decimal("1300000")
    assert data["top_paquetes"][0]["paquete"] == package["nombre"]

    xlsx = client.get("/reports/export?formato=xlsx&desde=2025-06-01&hasta=2027-12-31", headers=auth(admin_token))
    assert xlsx.status_code == 200 and xlsx.content.startswith(b"PK")

    pdf = client.get("/reports/export?formato=pdf", headers=auth(admin_token))
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    assert client.get("/reports/summary", headers=auth(client_token)).status_code == 403
    assert client.get("/reports/summary?desde=2026-05-01&hasta=2026-01-01", headers=auth(admin_token)).status_code == 400

from datetime import date
from decimal import Decimal

from app.models.provider_payment_order_model import ProviderPaymentOrderModel
from app.models.user_model import UserModel

from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
    login_user,
)

# El helper crea: proveedor aprobado "proveedor_reserva@example.com" con
# "Producto Reserva" (costo 150.000, por persona) incluido 1 vez en el paquete.
# Paquete: viaje del 2026-09-10, precio 650.000.
PRODUCT_COST = Decimal("150000")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


BANK_DATA = {"banco": "Bancolombia", "tipo_cuenta": "ahorros", "numero_cuenta": "123-456789-01", "titular_cuenta": "Proveedor Reserva SAS"}


def save_bank_data(client, provider_token):
    provider = client.get("/providers/me", headers=auth(provider_token)).json()
    response = client.patch(f"/providers/{provider['id_proveedor']}", json=BANK_DATA, headers=auth(provider_token))
    assert response.status_code == 200, response.json()


def setup(client, db_session, email="viajero_op@example.com", identificacion="700100200", with_bank=True):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(client, db_session, email=email, identificacion=identificacion)
    provider_token = login_user(client, "proveedor_reserva@example.com")
    # Sin datos bancarios no se pueden aprobar ni pagar órdenes
    if with_bank:
        save_bank_data(client, provider_token)
    return package, admin_token, client_token, provider_token


def book_and_pay(client, token, package_id, people=2, pay=True):
    companions = [
        {"nombre": f"Acompañante {i}", "documento": f"55500{i}", "fecha_nacimiento": "1995-04-15"}
        for i in range(people - 1)
    ]
    reservation = create_reservation(client, token, package_id, cantidad_personas=people, acompanantes=companions).json()

    if pay:
        response = client.post(
            "/payments/",
            json={"reserva_id": reservation["id_reserva"], "metodo_pago": "tarjeta", "valor": reservation["total_reserva"]},
            headers=auth(token),
        )
        assert response.status_code == 201, response.json()

    return reservation


def package_product_id(client, admin_token, package_id):
    return client.get(f"/packages/admin/{package_id}", headers=auth(admin_token)).json()["productos"][0]["producto_id"]


# ---------------------------------------------------------------
# Generación automática
# ---------------------------------------------------------------

def test_paying_a_reservation_creates_provider_order(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"], people=2)

    orders = client.get("/provider-payments/me", headers=auth(provider_token)).json()

    assert len(orders) == 1
    order = orders[0]
    assert order["estado"] == "pendiente"
    assert order["codigo"].startswith("OP-")
    assert order["codigo_reserva"] == reservation["codigo_reserva"]
    assert order["paquete"] == package["nombre"]
    assert order["viajeros"] == 2
    assert Decimal(order["monto"]) == PRODUCT_COST * 2
    assert order["fecha_vencimiento"] == "2026-09-25"  # viaje + 15 días
    assert order["detalles"][0]["descripcion"] == "Producto Reserva"
    assert order["detalles"][0]["viajeros"] == 2

    admin_orders = client.get("/provider-payments/", headers=auth(admin_token)).json()
    assert [item["id_orden"] for item in admin_orders] == [order["id_orden"]]


def test_unpaid_reservation_has_no_order(client, db_session):
    package, _, client_token, provider_token = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"], pay=False)

    assert client.get("/provider-payments/me", headers=auth(provider_token)).json() == []


def test_service_unit_is_not_multiplied_by_travelers(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    product_id = package_product_id(client, admin_token, package["id_paquete_turistico"])
    client.patch(f"/products/{product_id}", json={"unidad_cobro": "servicio"}, headers=auth(admin_token))

    book_and_pay(client, client_token, package["id_paquete_turistico"], people=3)
    order = client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]

    assert Decimal(order["monto"]) == PRODUCT_COST
    assert order["detalles"][0]["viajeros"] == 1


def test_amount_uses_package_quantity(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    package_id = package["id_paquete_turistico"]
    product_id = package_product_id(client, admin_token, package_id)
    client.patch(
        f"/packages/{package_id}",
        json={"productos": [{"producto_id": product_id, "cantidad": 3}]},
        headers=auth(admin_token),
    )

    book_and_pay(client, client_token, package_id, people=2)
    order = client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]

    assert Decimal(order["monto"]) == PRODUCT_COST * 3 * 2


def test_client_cancellation_annuls_pending_orders(client, db_session):
    package, _, client_token, provider_token = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])

    client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=auth(client_token))
    order = client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]

    assert order["estado"] == "anulada"
    assert "cancelada" in order["nota"]


def test_admin_status_changes_keep_orders_in_sync(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"], pay=False)
    url = f"/reservations/{reservation['id_reserva']}/status"

    client.patch(url, json={"estado": "confirmada"}, headers=auth(admin_token))
    assert client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]["estado"] == "pendiente"

    client.patch(url, json={"estado": "cancelada"}, headers=auth(admin_token))
    assert client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]["estado"] == "anulada"


# ---------------------------------------------------------------
# Flujo del administrador
# ---------------------------------------------------------------

def test_admin_approves_and_pays_order(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order_id = client.get("/provider-payments/", headers=auth(admin_token)).json()[0]["id_orden"]

    approved = client.patch(f"/provider-payments/{order_id}/approve", headers=auth(admin_token))
    assert approved.json()["estado"] == "aprobada"

    paid = client.patch(
        f"/provider-payments/{order_id}/pay",
        json={"referencia_pago": "TRF-2026-0001", "nota": "Transferencia Bancolombia"},
        headers=auth(admin_token),
    )
    assert paid.status_code == 200, paid.json()
    assert paid.json()["estado"] == "pagada"
    assert paid.json()["referencia_pago"] == "TRF-2026-0001"
    assert paid.json()["fecha_pago"] is not None

    # Una orden pagada ya no se paga, aprueba ni anula
    assert client.patch(f"/provider-payments/{order_id}/pay", json={"referencia_pago": "X-1"}, headers=auth(admin_token)).status_code == 400
    assert client.patch(f"/provider-payments/{order_id}/annul", json={"nota": "error"}, headers=auth(admin_token)).status_code == 400


def test_paid_order_survives_reservation_cancellation(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])
    order_id = client.get("/provider-payments/", headers=auth(admin_token)).json()[0]["id_orden"]
    client.patch(f"/provider-payments/{order_id}/pay", json={"referencia_pago": "TRF-9"}, headers=auth(admin_token))

    client.patch(f"/reservations/{reservation['id_reserva']}/cancel", headers=auth(client_token))

    assert client.get(f"/provider-payments/{order_id}", headers=auth(admin_token)).json()["estado"] == "pagada"


def test_admin_can_annul_with_note(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order_id = client.get("/provider-payments/", headers=auth(admin_token)).json()[0]["id_orden"]

    response = client.patch(f"/provider-payments/{order_id}/annul", json={"nota": "Servicio no prestado"}, headers=auth(admin_token))

    assert response.json()["estado"] == "anulada"
    assert response.json()["nota"] == "Servicio no prestado"


def test_admin_filters_orders(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])

    assert len(client.get("/provider-payments/?estado=pendiente", headers=auth(admin_token)).json()) == 1
    assert client.get("/provider-payments/?estado=pagada", headers=auth(admin_token)).json() == []


def test_generate_missing_orders_for_old_reservations(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])

    # Simula una reserva confirmada de antes de que existieran las órdenes
    db_session.rollback()
    db_session.query(ProviderPaymentOrderModel).delete()
    db_session.commit()

    first = client.post("/provider-payments/generate", headers=auth(admin_token)).json()
    second = client.post("/provider-payments/generate", headers=auth(admin_token)).json()

    assert first == {"ordenes_creadas": 1}
    assert second == {"ordenes_creadas": 0}


# ---------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------

def test_provider_cannot_manage_orders(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order_id = client.get("/provider-payments/", headers=auth(admin_token)).json()[0]["id_orden"]

    assert client.get("/provider-payments/", headers=auth(provider_token)).status_code == 403
    assert client.patch(f"/provider-payments/{order_id}/approve", headers=auth(provider_token)).status_code == 403
    assert client.patch(f"/provider-payments/{order_id}/pay", json={"referencia_pago": "X-123"}, headers=auth(provider_token)).status_code == 403
    assert client.get(f"/provider-payments/{order_id}", headers=auth(provider_token)).status_code == 200


def test_client_cannot_see_provider_orders(client, db_session):
    package, admin_token, client_token, _ = setup(client, db_session)
    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order_id = client.get("/provider-payments/", headers=auth(admin_token)).json()[0]["id_orden"]

    assert client.get("/provider-payments/me", headers=auth(client_token)).status_code == 403
    assert client.get(f"/provider-payments/{order_id}", headers=auth(client_token)).status_code == 403


# ---------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------

def test_payment_term_setting_changes_due_date(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)

    assert client.get("/settings/", headers=auth(admin_token)).json() == {
        "dias_pago_proveedores": 15,
        "dias_cancelacion_gratis": 7,
        "porcentaje_penalidad_cancelacion": 30,
        "dias_recordatorio_viaje": 3,
        "horas_para_pagar": 24,
        "dia_pago_proveedores": 15,
    }

    updated = client.patch("/settings/", json={"dias_pago_proveedores": 30}, headers=auth(admin_token))
    assert updated.json()["dias_pago_proveedores"] == 30

    book_and_pay(client, client_token, package["id_paquete_turistico"])
    order = client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]
    assert order["fecha_vencimiento"] == "2026-10-10"


def test_settings_are_admin_only(client, db_session):
    _, _, client_token, _ = setup(client, db_session)

    assert client.get("/settings/", headers=auth(client_token)).status_code == 403
    assert client.patch("/settings/", json={"dias_pago_proveedores": 1}, headers=auth(client_token)).status_code == 403


# ---------------------------------------------------------------
# Unidad de cobro y datos bancarios
# ---------------------------------------------------------------

def test_product_units_catalog_and_validation(client, db_session):
    package, admin_token, _, _ = setup(client, db_session)
    product_id = package_product_id(client, admin_token, package["id_paquete_turistico"])

    units = [unit["clave"] for unit in client.get("/products/units").json()]
    assert units == ["persona", "noche", "dia", "servicio"]

    assert client.patch(f"/products/{product_id}", json={"unidad_cobro": "semana"}, headers=auth(admin_token)).status_code == 422
    ok = client.patch(f"/products/{product_id}", json={"unidad_cobro": "Noche"}, headers=auth(admin_token))
    assert ok.json()["unidad_cobro"] == "noche"


def test_provider_saves_bank_details(client, db_session):
    _, _, _, provider_token = setup(client, db_session)
    provider = client.get("/providers/me", headers=auth(provider_token)).json()
    url = f"/providers/{provider['id_proveedor']}"

    bad = client.patch(url, json={"tipo_cuenta": "nomina"}, headers=auth(provider_token))
    good = client.patch(
        url,
        json={"banco": "Bancolombia", "tipo_cuenta": "ahorros", "numero_cuenta": "123-456789-01", "titular_cuenta": "Proveedor Reserva SAS"},
        headers=auth(provider_token),
    )

    assert bad.status_code == 422
    assert good.status_code == 200, good.json()
    assert good.json()["banco"] == "Bancolombia"
    assert good.json()["numero_cuenta"] == "123-456789-01"


# ---------------------------------------------------------------
# Registro como proveedor
# ---------------------------------------------------------------

def new_user_payload(email, rut="800900100"):
    return {
        "nombre": "Empresa Nueva",
        "email": email,
        "password": "123456",
        "proveedor": {
            "rut": rut,
            "telefono": "3001234567",
            "direccion": "Carrera 7 # 10-20",
            "nombre_empresa": "Transportes del Valle",
            "ciudad_id": 1,
        },
    }


def test_register_as_provider_creates_pending_request(client, db_session):
    package, admin_token, _, _ = setup(client, db_session)

    response = client.post("/users/", json=new_user_payload("transportes@example.com"))

    assert response.status_code == 201, response.json()
    assert response.json()["rol_id"] == 2  # sigue siendo cliente hasta la aprobación

    pending = client.get("/providers/pending", headers=auth(admin_token)).json()
    assert "Transportes del Valle" in [item["nombre_empresa"] for item in pending]


def test_register_with_taken_rut_does_not_create_user(client, db_session):
    client.post("/users/", json=new_user_payload("primero@example.com", rut="811811811"))

    response = client.post("/users/", json=new_user_payload("segundo@example.com", rut="811811811"))

    assert response.status_code == 400
    db_session.rollback()
    assert db_session.query(UserModel).filter(UserModel.email == "segundo@example.com").first() is None


def test_register_without_provider_still_works(client):
    response = client.post("/users/", json={"nombre": "Viajero Normal", "email": "normal_reg@example.com", "password": "123456"})

    assert response.status_code == 201


def test_cancelled_reservation_cannot_be_reactivated(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"], pay=False)
    url = f"/reservations/{reservation['id_reserva']}/status"

    assert client.patch(url, json={"estado": "cancelada"}, headers=auth(admin_token)).status_code == 200

    for estado in ("confirmada", "pendiente"):
        response = client.patch(url, json={"estado": estado}, headers=auth(admin_token))
        assert response.status_code == 400
        assert "cancelada" in response.json()["detail"]


def test_cancellation_policy_is_configurable(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)

    response = client.patch(
        "/settings/",
        json={"dias_cancelacion_gratis": 10, "porcentaje_penalidad_cancelacion": 50},
        headers=auth(admin_token),
    )
    assert response.status_code == 200

    policy = client.get("/reservations/cancellation-policy").json()
    assert policy == {"dias_sin_penalidad": 10, "porcentaje_penalidad": 50, "horas_para_pagar": 24}

    assert client.patch("/settings/", json={"porcentaje_penalidad_cancelacion": 150}, headers=auth(admin_token)).status_code == 422


def test_admin_cancellation_refunds_full_payment(client, db_session):
    package, admin_token, client_token, provider_token = setup(client, db_session)
    reservation = book_and_pay(client, client_token, package["id_paquete_turistico"])

    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/status",
        json={"estado": "cancelada"},
        headers=auth(admin_token),
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["estado"] == "cancelada"
    assert float(data["penalidad_cancelacion"]) == 0
    assert float(data["reembolso"]) == float(reservation["total_reserva"])

    payment = client.get("/payments/", headers=auth(admin_token)).json()[0]
    assert payment["estado_pago"] == "reembolsado"
    assert client.get("/provider-payments/me", headers=auth(provider_token)).json()[0]["estado"] == "anulada"

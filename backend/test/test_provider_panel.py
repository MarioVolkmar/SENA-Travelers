from test_reservations import (
    approve_provider,
    create_admin_with_token,
    create_client_with_token,
    create_package_ready_for_reservation,
    create_provider_profile,
    create_reservation,
    create_verified_user,
    login_user,
)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def provider_request_data(rut="960960960", nombre="Hotel Sol"):
    return {
        "rut": rut,
        "telefono": "3001234567",
        "direccion": "Calle 10 # 20-30",
        "nombre_empresa": nombre,
        "ciudad_id": 1,
    }


# ---------------------------------------------------------------
# Catálogo de tipos de producto
# ---------------------------------------------------------------

def test_product_types_catalog(client):
    types = client.get("/products/types").json()

    keys = [item["clave"] for item in types]
    assert keys[:3] == ["hospedaje", "alimentacion", "transporte"]
    assert "otro" in keys
    assert all(item["nombre"] and item["ejemplos"] for item in types)


def test_product_type_must_be_in_catalog(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    provider_id = client.get("/providers/", headers=auth(admin_token)).json()[0]["id_proveedor"]

    base = {
        "nombre": "Cena típica",
        "descripcion": "Cena de tres tiempos con platos típicos de la región",
        "costo": "80000",
        "ciudad_id": 1,
        "proveedor_id": provider_id,
    }

    invalid = client.post("/products/", json={**base, "tipo_producto": "viaje"}, headers=auth(admin_token))
    valid = client.post("/products/", json={**base, "tipo_producto": " Alimentacion "}, headers=auth(admin_token))

    assert invalid.status_code == 422
    assert valid.status_code == 201, valid.json()
    assert valid.json()["tipo_producto"] == "alimentacion"


# ---------------------------------------------------------------
# Solicitud para ser proveedor
# ---------------------------------------------------------------

def test_user_without_request_has_no_dashboard(client, db_session):
    create_verified_user(client, db_session, nombre="Sin Solicitud", email="sin_solicitud@example.com")
    token = login_user(client, "sin_solicitud@example.com")

    assert client.get("/providers/me/dashboard", headers=auth(token)).status_code == 404


def test_pending_provider_sees_only_request_status(client, db_session):
    create_verified_user(client, db_session, nombre="Pendiente", email="pendiente_prov@example.com")
    token = login_user(client, "pendiente_prov@example.com")
    client.post("/providers/me", json=provider_request_data(), headers=auth(token))

    dashboard = client.get("/providers/me/dashboard", headers=auth(token)).json()

    assert dashboard["proveedor"]["estado_verificacion"] == "pendiente"
    assert dashboard["productos"] == []
    assert dashboard["paquetes"] == []


def test_rejected_provider_can_resubmit_request(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)
    create_verified_user(client, db_session, nombre="Rechazado", email="rechazado@example.com")
    token = login_user(client, "rechazado@example.com")
    provider = client.post("/providers/me", json=provider_request_data(), headers=auth(token)).json()

    client.patch(
        f"/providers/{provider['id_proveedor']}/verification-status",
        json={"estado_verificacion": "rechazado"},
        headers=auth(admin_token),
    )

    response = client.post(
        "/providers/me",
        json=provider_request_data(rut="960960961", nombre="Hotel Sol Renovado"),
        headers=auth(token),
    )

    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["id_proveedor"] == provider["id_proveedor"]
    assert data["estado_verificacion"] == "pendiente"
    assert data["nombre_empresa"] == "Hotel Sol Renovado"
    assert data["fecha_verificacion"] is None


def test_pending_request_cannot_be_sent_twice(client, db_session):
    create_verified_user(client, db_session, nombre="Doble", email="doble@example.com")
    token = login_user(client, "doble@example.com")
    client.post("/providers/me", json=provider_request_data(), headers=auth(token))

    again = client.post("/providers/me", json=provider_request_data(rut="970970970"), headers=auth(token))

    assert again.status_code == 400


def test_admin_cannot_request_to_be_provider(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)

    response = client.post("/providers/me", json=provider_request_data(), headers=auth(admin_token))

    assert response.status_code == 403


# ---------------------------------------------------------------
# Panel del proveedor aprobado
# ---------------------------------------------------------------

def test_approved_provider_dashboard_shows_packages_and_travelers(client, db_session):
    # El helper crea un proveedor aprobado (proveedor_reserva@example.com) con un producto en el paquete
    package, _ = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(
        client, db_session, email="viajero_prov@example.com", identificacion="980980980"
    )

    reservation = create_reservation(client, client_token, package["id_paquete_turistico"], cantidad_personas=2).json()
    client.post(
        "/payments/",
        json={"reserva_id": reservation["id_reserva"], "metodo_pago": "tarjeta", "valor": reservation["total_reserva"]},
        headers=auth(client_token),
    )
    create_reservation(client, client_token, package["id_paquete_turistico"], cantidad_personas=1, acompanantes=[])

    provider_token = login_user(client, "proveedor_reserva@example.com")
    dashboard = client.get("/providers/me/dashboard", headers=auth(provider_token)).json()

    assert dashboard["proveedor"]["estado_verificacion"] == "aprobado"
    assert [product["nombre"] for product in dashboard["productos"]] == ["Producto Reserva"]
    assert dashboard["resumen"] == {"productos_activos": 1, "paquetes": 1, "viajeros_proximos": 2}

    item = dashboard["paquetes"][0]
    assert item["id_paquete_turistico"] == package["id_paquete_turistico"]
    assert item["productos"] == ["Producto Reserva"]
    assert item["viajeros_confirmados"] == 2
    assert item["reservas_confirmadas"] == 1
    assert item["viajeros_pendientes"] == 1


def test_provider_creates_and_edits_own_products(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)
    create_verified_user(client, db_session, nombre="Hotelero", email="hotelero@example.com")
    token = login_user(client, "hotelero@example.com")
    provider = create_provider_profile(client, token, rut="990990990", nombre_empresa="Hotel Mar")
    approve_provider(client, admin_token, provider["id_proveedor"])
    token = login_user(client, "hotelero@example.com")  # el rol cambió al aprobarlo

    created = client.post(
        "/products/",
        json={
            "nombre": "Habitación doble",
            "descripcion": "Habitación doble con vista al mar y desayuno",
            "tipo_producto": "hospedaje",
            "costo": "250000",
            "ciudad_id": 1,
            "proveedor_id": provider["id_proveedor"],
        },
        headers=auth(token),
    )
    assert created.status_code == 201, created.json()
    product_id = created.json()["id_producto"]

    edited = client.patch(f"/products/{product_id}", json={"costo": "270000"}, headers=auth(token))
    paused = client.patch(f"/products/{product_id}/status", json={"estado": "inactivo"}, headers=auth(token))

    assert edited.status_code == 200
    assert paused.json()["estado"] == "inactivo"

    dashboard = client.get("/providers/me/dashboard", headers=auth(token)).json()
    assert dashboard["resumen"]["productos_activos"] == 0
    assert len(dashboard["productos"]) == 1

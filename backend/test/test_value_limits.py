"""Límites razonables de precios, costos, cupos, descuentos y cantidades (constants.py)."""
from app.core.constants import (
    PACKAGE_DISCOUNT_MAX,
    PACKAGE_PRICE_MAX,
    PACKAGE_PRODUCT_QUANTITY_MAX,
    PACKAGE_SLOTS_MAX,
    PRODUCT_COST_MAX,
)

from test_packages import create_admin_with_token, create_approved_provider_with_product


def setup_admin(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)
    provider, product = create_approved_provider_with_product(client, db_session, admin_token)
    return admin_token, provider, product


def package_payload(product_id, **changes):
    data = {
        "nombre": "Paquete con límites",
        "descripcion": "Paquete turístico de prueba con varios servicios incluidos.",
        "precio": "650000.00",
        "descuento": 0,
        "fecha_inicio": "2026-09-10",
        "fecha_fin": "2026-09-12",
        "cupo_max": 20,
        "ciudad_id": 1,
        "productos": [{"producto_id": product_id, "cantidad": 1}],
    }
    data.update(changes)
    return data


def create(client, token, payload):
    return client.post("/packages/", json=payload, headers={"Authorization": f"Bearer {token}"})


def test_package_price_above_limit_is_rejected(client, db_session):
    token, _, product = setup_admin(client, db_session)

    response = create(client, token, package_payload(product["id_producto"], precio=str(PACKAGE_PRICE_MAX + 1)))

    assert response.status_code == 400
    assert "precio por persona" in response.json()["detail"]


def test_package_price_at_the_limit_is_accepted(client, db_session):
    token, _, product = setup_admin(client, db_session)

    response = create(client, token, package_payload(product["id_producto"], precio=str(PACKAGE_PRICE_MAX)))

    assert response.status_code == 201, response.json()


def test_package_slots_and_discount_limits(client, db_session):
    token, _, product = setup_admin(client, db_session)

    too_many = create(client, token, package_payload(product["id_producto"], cupo_max=PACKAGE_SLOTS_MAX + 1))
    too_much_discount = create(client, token, package_payload(product["id_producto"], descuento=PACKAGE_DISCOUNT_MAX + 1))

    assert too_many.status_code == 400 and "cupo" in too_many.json()["detail"]
    assert too_much_discount.status_code == 400 and "descuento" in too_much_discount.json()["detail"]


def test_product_quantity_inside_package_is_limited(client, db_session):
    token, _, product = setup_admin(client, db_session)

    response = create(client, token, package_payload(
        product["id_producto"],
        productos=[{"producto_id": product["id_producto"], "cantidad": PACKAGE_PRODUCT_QUANTITY_MAX + 1}],
    ))

    assert response.status_code == 400
    assert "cantidad" in response.json()["detail"]


def test_editing_package_with_huge_price_is_rejected(client, db_session):
    token, _, product = setup_admin(client, db_session)
    package = create(client, token, package_payload(product["id_producto"])).json()

    response = client.patch(
        f"/packages/{package['id_paquete_turistico']}",
        json={"precio": "999999999"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (400, 422)


def test_product_cost_limit_on_create_and_edit(client, db_session):
    token, provider, product = setup_admin(client, db_session)
    auth = {"Authorization": f"Bearer {token}"}

    created = client.post("/products/", json={
        "nombre": "Producto carísimo",
        "descripcion": "Producto con costo fuera de lo razonable.",
        "tipo_producto": "hospedaje",
        "costo": str(PRODUCT_COST_MAX + 1),
        "ciudad_id": 1,
        "proveedor_id": provider["id_proveedor"],
        "unidad_cobro": "noche",
    }, headers=auth)
    edited = client.patch(f"/products/{product['id_producto']}", json={"costo": str(PRODUCT_COST_MAX + 1)}, headers=auth)
    ok = client.patch(f"/products/{product['id_producto']}", json={"costo": str(PRODUCT_COST_MAX)}, headers=auth)

    assert created.status_code == 400 and "costo" in created.json()["detail"]
    assert edited.status_code == 400
    assert ok.status_code == 200, ok.json()

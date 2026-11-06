import pytest

from app.core import storage

from test_reservations import (
    create_admin_with_token,
    create_client_with_token,
    create_package_ready_for_reservation,
    create_product,
    create_provider_profile,
    approve_provider,
    create_verified_user,
    login_user,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType, CacheControl):
        self.objects[Key] = Body

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)


@pytest.fixture(autouse=True)
def fake_s3(monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(storage, "s3_client", lambda: s3)
    monkeypatch.setenv("S3_BUCKET", "travelers-test")
    monkeypatch.setenv("CLOUDFRONT_URL", "https://cdn.travelers.test")
    return s3


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def second_product(client, db_session, admin_token):
    create_verified_user(client, db_session, nombre="Proveedor Dos", email="proveedor_dos@example.com")
    provider_token = login_user(client, "proveedor_dos@example.com")
    provider = create_provider_profile(client, provider_token, rut="930930930", nombre_empresa="Proveedor Dos")
    approve_provider(client, admin_token, provider["id_proveedor"])
    return create_product(client, admin_token, proveedor_id=provider["id_proveedor"], nombre="Producto Dos")


# ---------------------------------------------------------------
# Paquetes: detalle y edición de productos
# ---------------------------------------------------------------

def test_admin_package_detail_includes_products(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)

    detail = client.get(f"/packages/admin/{package['id_paquete_turistico']}", headers=auth(admin_token)).json()

    assert detail["nombre"] == package["nombre"]
    assert len(detail["productos"]) == 1
    assert detail["productos"][0]["cantidad"] == 1


def test_admin_can_replace_package_products(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    product = second_product(client, db_session, admin_token)
    package_id = package["id_paquete_turistico"]

    response = client.patch(
        f"/packages/{package_id}",
        json={"productos": [{"producto_id": product["id_producto"], "cantidad": 2}]},
        headers=auth(admin_token),
    )

    assert response.status_code == 200, response.json()
    detail = client.get(f"/packages/admin/{package_id}", headers=auth(admin_token)).json()
    assert detail["productos"] == [{"producto_id": product["id_producto"], "cantidad": 2}]


def test_package_update_rejects_repeated_products(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    detail = client.get(f"/packages/admin/{package['id_paquete_turistico']}", headers=auth(admin_token)).json()
    product_id = detail["productos"][0]["producto_id"]

    response = client.patch(
        f"/packages/{package['id_paquete_turistico']}",
        json={"productos": [{"producto_id": product_id}, {"producto_id": product_id}]},
        headers=auth(admin_token),
    )

    assert response.status_code == 400


def test_package_update_can_change_data_and_products_together(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    product = second_product(client, db_session, admin_token)

    response = client.patch(
        f"/packages/{package['id_paquete_turistico']}",
        json={"nombre": "Paquete Renovado", "productos": [{"producto_id": product["id_producto"]}]},
        headers=auth(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["nombre"] == "Paquete Renovado"


# ---------------------------------------------------------------
# Imágenes de paquetes subidas a S3 desde la consola
# ---------------------------------------------------------------

def upload_image(client, token, package_id, data=PNG, es_portada=False):
    return client.post(
        f"/packages/{package_id}/images/upload",
        files={"file": ("foto.png", data, "image/png")},
        data={"es_portada": str(es_portada).lower(), "orden": "0"},
        headers=auth(token),
    )


def test_admin_uploads_package_image_to_s3(client, db_session, fake_s3):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    response = upload_image(client, admin_token, package_id, es_portada=True)

    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["s3_key"].startswith(f"{package_id}/")
    assert data["es_portada"] is True
    assert data["imagen_url"] == f"https://cdn.travelers.test/{data['s3_key']}"
    assert fake_s3.objects[data["s3_key"]] == PNG


def test_client_cannot_upload_package_image(client, db_session, fake_s3):
    package, _ = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(client, db_session, email="cli_img@example.com", identificacion="940940940")

    response = upload_image(client, client_token, package["id_paquete_turistico"])

    assert response.status_code == 403
    assert fake_s3.objects == {}


def test_upload_rejects_non_images(client, db_session, fake_s3):
    package, admin_token = create_package_ready_for_reservation(client, db_session)

    response = upload_image(client, admin_token, package["id_paquete_turistico"], data=b"no es imagen")

    assert response.status_code == 400
    assert fake_s3.objects == {}


def test_deleting_uploaded_image_removes_it_from_s3(client, db_session, fake_s3):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]
    image = upload_image(client, admin_token, package_id).json()

    response = client.delete(f"/packages/{package_id}/images/{image['id_imagen']}", headers=auth(admin_token))

    assert response.status_code == 204
    assert fake_s3.objects == {}


def test_deleting_manually_registered_image_keeps_s3_file(client, db_session, fake_s3):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]
    fake_s3.objects[f"{package_id}/portada.jpg"] = b"manual"

    image = client.post(
        f"/packages/{package_id}/images",
        json={"s3_key": f"{package_id}/portada.jpg"},
        headers=auth(admin_token),
    ).json()
    client.delete(f"/packages/{package_id}/images/{image['id_imagen']}", headers=auth(admin_token))

    assert f"{package_id}/portada.jpg" in fake_s3.objects


# ---------------------------------------------------------------
# Ciudades
# ---------------------------------------------------------------

def test_admin_can_create_city(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)

    response = client.post(
        "/cities/",
        json={"nombre": "Pereira", "departamento": "Risaralda"},
        headers=auth(admin_token),
    )

    assert response.status_code == 201, response.json()
    assert response.json()["pais"] == "Colombia"
    assert "Pereira" in [city["nombre"] for city in client.get("/cities/").json()]


def test_city_cannot_be_duplicated(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)

    response = client.post(
        "/cities/",
        json={"nombre": "medellín", "departamento": "ANTIOQUIA"},
        headers=auth(admin_token),
    )

    assert response.status_code == 400


def test_client_cannot_create_city(client, db_session):
    client_token, _ = create_client_with_token(client, db_session, email="cli_city@example.com", identificacion="950950950")

    response = client.post(
        "/cities/",
        json={"nombre": "Pereira", "departamento": "Risaralda"},
        headers=auth(client_token),
    )

    assert response.status_code == 403

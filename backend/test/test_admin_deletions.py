import pytest

from app.core import storage
from app.models.notification_email_model import NotificationEmailModel
from app.models.user_model import UserModel

from test_reservations import (
    create_admin_with_token,
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
    create_verified_user,
    login_user,
)


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
    return s3


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def provider_request(rut="550550550"):
    return {
        "rut": rut,
        "telefono": "3001234567",
        "direccion": "Calle 10 # 20-30",
        "nombre_empresa": "Empresa Rechazada",
        "ciudad_id": 1,
    }


def rejected_provider(client, db_session, admin_token, email="rechazada@example.com"):
    create_verified_user(client, db_session, nombre="Empresa Rechazada", email=email)
    token = login_user(client, email)
    provider = client.post("/providers/me", json=provider_request(), headers=auth(token)).json()
    client.patch(
        f"/providers/{provider['id_proveedor']}/verification-status",
        json={"estado_verificacion": "rechazado"},
        headers=auth(admin_token),
    )
    return provider


# ---------------------------------------------------------------
# Proveedores
# ---------------------------------------------------------------

def test_admin_deletes_rejected_provider_but_keeps_user(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)
    provider = rejected_provider(client, db_session, admin_token)

    response = client.delete(f"/providers/{provider['id_proveedor']}", headers=auth(admin_token))

    assert response.status_code == 204
    assert provider["id_proveedor"] not in [item["id_proveedor"] for item in client.get("/providers/", headers=auth(admin_token)).json()]
    # La cuenta sigue existiendo y puede volver a solicitar
    token = login_user(client, "rechazada@example.com")
    assert client.post("/providers/me", json=provider_request("560560560"), headers=auth(token)).status_code == 201


def test_approved_provider_cannot_be_deleted(client, db_session):
    _, admin_token = create_package_ready_for_reservation(client, db_session)
    provider = client.get("/providers/", headers=auth(admin_token)).json()[0]

    response = client.delete(f"/providers/{provider['id_proveedor']}", headers=auth(admin_token))

    assert response.status_code == 409
    assert "rechazados" in response.json()["detail"]


def test_rejected_provider_with_products_cannot_be_deleted(client, db_session):
    _, admin_token = create_package_ready_for_reservation(client, db_session)
    provider = client.get("/providers/", headers=auth(admin_token)).json()[0]
    client.patch(
        f"/providers/{provider['id_proveedor']}/verification-status",
        json={"estado_verificacion": "rechazado"},
        headers=auth(admin_token),
    )

    response = client.delete(f"/providers/{provider['id_proveedor']}", headers=auth(admin_token))

    assert response.status_code == 409
    assert "producto" in response.json()["detail"]


# ---------------------------------------------------------------
# Paquetes
# ---------------------------------------------------------------

def test_admin_deletes_package_without_reservations_and_its_uploaded_photos(client, db_session, fake_s3):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]
    uploaded = client.post(
        f"/packages/{package_id}/images/upload",
        files={"file": ("f.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 16, "image/png")},
        headers=auth(admin_token),
    ).json()
    fake_s3.objects[f"{package_id}/manual.jpg"] = b"manual"
    client.post(f"/packages/{package_id}/images", json={"s3_key": f"{package_id}/manual.jpg"}, headers=auth(admin_token))

    response = client.delete(f"/packages/{package_id}", headers=auth(admin_token))

    assert response.status_code == 204
    assert client.get(f"/packages/admin/{package_id}", headers=auth(admin_token)).status_code == 404
    assert uploaded["s3_key"] not in fake_s3.objects  # subida por la consola: se borra
    assert f"{package_id}/manual.jpg" in fake_s3.objects  # cargada a mano: se conserva


def test_package_with_reservations_cannot_be_deleted(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(client, db_session, email="cli_del@example.com", identificacion="560560561")
    create_reservation(client, client_token, package["id_paquete_turistico"], cantidad_personas=1, acompanantes=[])

    response = client.delete(f"/packages/{package['id_paquete_turistico']}", headers=auth(admin_token))

    assert response.status_code == 409
    assert "Desactívalo" in response.json()["detail"]


# ---------------------------------------------------------------
# Productos
# ---------------------------------------------------------------

def test_product_in_package_cannot_be_deleted_until_removed(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    product_id = client.get(f"/packages/admin/{package['id_paquete_turistico']}", headers=auth(admin_token)).json()["productos"][0]["producto_id"]

    blocked = client.delete(f"/products/{product_id}", headers=auth(admin_token))
    assert blocked.status_code == 409
    assert "paquete" in blocked.json()["detail"]

    # Sin el paquete, el producto ya se puede borrar
    client.delete(f"/packages/{package['id_paquete_turistico']}", headers=auth(admin_token))
    assert client.delete(f"/products/{product_id}", headers=auth(admin_token)).status_code == 204
    assert client.get(f"/products/admin/{product_id}", headers=auth(admin_token)).status_code == 404


# ---------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------

def test_admin_deletes_user_with_profile_and_notifications(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)
    client_token, _ = create_client_with_token(client, db_session, email="borrar@example.com", identificacion="570570570")
    user_id = client.get("/users/me", headers=auth(client_token)).json()["id_usuario"]

    response = client.delete(f"/users/{user_id}", headers=auth(admin_token))

    assert response.status_code == 204
    db_session.rollback()
    assert db_session.query(UserModel).filter(UserModel.id_usuario == user_id).first() is None
    assert db_session.query(NotificationEmailModel).filter(NotificationEmailModel.usuarios_id_usuario == user_id).count() == 0


def test_user_with_reservations_cannot_be_deleted(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(client, db_session, email="con_reserva@example.com", identificacion="580580580")
    create_reservation(client, client_token, package["id_paquete_turistico"], cantidad_personas=1, acompanantes=[])
    user_id = client.get("/users/me", headers=auth(client_token)).json()["id_usuario"]

    response = client.delete(f"/users/{user_id}", headers=auth(admin_token))

    assert response.status_code == 409
    assert "reserva" in response.json()["detail"]


def test_admin_cannot_delete_own_account(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    response = client.delete(f"/users/{admin.id_usuario}", headers=auth(admin_token))

    assert response.status_code == 409


# ---------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------

def test_only_admin_can_delete(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(client, db_session, email="no_admin@example.com", identificacion="590590590")
    provider_token = login_user(client, "proveedor_reserva@example.com")
    product_id = client.get(f"/packages/admin/{package['id_paquete_turistico']}", headers=auth(admin_token)).json()["productos"][0]["producto_id"]

    for token in (client_token, provider_token):
        assert client.delete(f"/packages/{package['id_paquete_turistico']}", headers=auth(token)).status_code == 403
        assert client.delete(f"/products/{product_id}", headers=auth(token)).status_code == 403
        assert client.delete("/users/1", headers=auth(token)).status_code == 403


def test_deleting_missing_items_returns_404(client, db_session):
    _, admin_token = create_admin_with_token(client, db_session)

    for url in ("/providers/9999", "/packages/9999", "/products/9999", "/users/9999"):
        assert client.delete(url, headers=auth(admin_token)).status_code == 404, url

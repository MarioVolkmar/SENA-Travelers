import pytest

from app.models.user_model import UserModel
from app.services import google_auth_service

from test_reservations import create_user, verify_user_email


FAKE_CREDENTIAL = "fake-google-id-token-for-tests"


@pytest.fixture()
def google_payload(monkeypatch):
    """Simula la verificación de Google: devuelve el payload que se configure."""
    payload = {
        "iss": "https://accounts.google.com",
        "email": "viajera@gmail.com",
        "email_verified": True,
        "name": "Viajera Google",
        "sub": "1234567890",
    }

    def fake_verify(credential):
        assert credential == FAKE_CREDENTIAL
        return payload

    monkeypatch.setattr(google_auth_service, "verify_google_credential", fake_verify)
    return payload


def google_login(client):
    return client.post("/users/google", json={"credential": FAKE_CREDENTIAL})


def find_user(db_session, email):
    db_session.expire_all()
    return db_session.query(UserModel).filter(UserModel.email == email).first()


def test_google_login_creates_verified_client(client, db_session, google_payload):
    response = google_login(client)

    assert response.status_code == 200, response.json()
    token = response.json()["access_token"]

    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["email"] == "viajera@gmail.com"
    assert me["nombre"] == "Viajera Google"
    assert me["rol_id"] == 2
    assert me["verificacion_email"] == "verificado"


def test_google_login_twice_reuses_the_same_user(client, db_session, google_payload):
    assert google_login(client).status_code == 200
    assert google_login(client).status_code == 200

    db_session.expire_all()
    assert db_session.query(UserModel).filter(UserModel.email == "viajera@gmail.com").count() == 1


def test_google_login_with_existing_email_logs_into_that_account(client, db_session, google_payload):
    create_user(client, "Cuenta Previa", "previa@gmail.com")
    verify_user_email(db_session, "previa@gmail.com")
    google_payload["email"] = "previa@gmail.com"

    response = google_login(client)

    assert response.status_code == 200
    me = client.get("/users/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"}).json()
    assert me["nombre"] == "Cuenta Previa"


def test_google_login_verifies_pending_account(client, db_session, google_payload):
    create_user(client, "Cuenta Pendiente", "pendiente@gmail.com")
    google_payload["email"] = "pendiente@gmail.com"

    assert google_login(client).status_code == 200
    assert find_user(db_session, "pendiente@gmail.com").verificacion_email == "verificado"


def test_google_login_rejects_inactive_user(client, db_session, google_payload):
    create_user(client, "Cuenta Inactiva", "inactiva@gmail.com")
    user = verify_user_email(db_session, "inactiva@gmail.com")
    user.estado = "inactivo"
    db_session.commit()
    google_payload["email"] = "inactiva@gmail.com"

    response = google_login(client)

    assert response.status_code == 401
    assert "inactivo" in response.json()["detail"]


def test_google_login_rejects_invalid_token(client, monkeypatch):
    def fake_verify(credential):
        raise PermissionError("El token de Google no es válido o expiró")

    monkeypatch.setattr(google_auth_service, "verify_google_credential", fake_verify)

    response = google_login(client)

    assert response.status_code == 401


def test_google_login_without_client_id_returns_503(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

    response = google_login(client)

    assert response.status_code == 503


def test_google_config_reports_client_id(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    assert client.get("/users/google/config").json() == {
        "enabled": True,
        "client_id": "abc.apps.googleusercontent.com",
    }

    monkeypatch.delenv("GOOGLE_CLIENT_ID")
    assert client.get("/users/google/config").json() == {"enabled": False, "client_id": None}


def test_unverified_google_email_is_rejected(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    monkeypatch.setattr(
        google_auth_service.id_token,
        "verify_oauth2_token",
        lambda credential, request, audience: {
            "iss": "accounts.google.com",
            "email": "x@gmail.com",
            "email_verified": False,
        },
    )

    with pytest.raises(PermissionError):
        google_auth_service.verify_google_credential(FAKE_CREDENTIAL)


def test_wrong_issuer_is_rejected(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    monkeypatch.setattr(
        google_auth_service.id_token,
        "verify_oauth2_token",
        lambda credential, request, audience: {
            "iss": "https://evil.example.com",
            "email": "x@gmail.com",
            "email_verified": True,
        },
    )

    with pytest.raises(PermissionError):
        google_auth_service.verify_google_credential(FAKE_CREDENTIAL)


# ---------------------------------------------------------------
# Cuentas de Google: vinculación y contraseña propia
# ---------------------------------------------------------------

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_new_google_account_is_linked_and_has_no_password(client, db_session, google_payload):
    token = google_login(client).json()["access_token"]

    me = client.get("/users/me", headers=auth_headers(token)).json()

    assert me["google_conectado"] is True
    assert me["tiene_contrasena"] is False


def test_existing_account_gets_linked_and_keeps_password(client, db_session, google_payload):
    create_user(client, "Cuenta Con Clave", "conclave@gmail.com")
    verify_user_email(db_session, "conclave@gmail.com")
    google_payload["email"] = "conclave@gmail.com"

    token = google_login(client).json()["access_token"]
    me = client.get("/users/me", headers=auth_headers(token)).json()

    assert me["google_conectado"] is True
    assert me["tiene_contrasena"] is True


def test_google_login_finds_user_by_sub_even_if_email_changed(client, db_session, google_payload):
    first = google_login(client).json()["access_token"]
    user_id = client.get("/users/me", headers=auth_headers(first)).json()["id_usuario"]

    google_payload["email"] = "nuevo.correo@gmail.com"
    second = google_login(client).json()["access_token"]

    assert client.get("/users/me", headers=auth_headers(second)).json()["id_usuario"] == user_id


def test_google_user_can_create_password_without_current_one(client, db_session, google_payload):
    token = google_login(client).json()["access_token"]
    user_id = client.get("/users/me", headers=auth_headers(token)).json()["id_usuario"]

    response = client.patch(
        f"/users/{user_id}/password",
        json={"new_password": "clave-nueva-123"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.json()
    assert response.json()["tiene_contrasena"] is True

    login = client.post("/users/login", json={"email": "viajera@gmail.com", "password": "clave-nueva-123"})
    assert login.status_code == 200


def test_after_creating_password_the_current_one_is_required(client, db_session, google_payload):
    token = google_login(client).json()["access_token"]
    user_id = client.get("/users/me", headers=auth_headers(token)).json()["id_usuario"]
    url = f"/users/{user_id}/password"

    client.patch(url, json={"new_password": "clave-nueva-123"}, headers=auth_headers(token))

    without_current = client.patch(url, json={"new_password": "otra-clave-456"}, headers=auth_headers(token))
    assert without_current.status_code == 403

    with_current = client.patch(
        url,
        json={"actual_password": "clave-nueva-123", "new_password": "otra-clave-456"},
        headers=auth_headers(token),
    )
    assert with_current.status_code == 200


def test_password_account_still_needs_current_password(client, db_session):
    create_user(client, "Cuenta Normal", "normal@example.com")
    user = verify_user_email(db_session, "normal@example.com")
    token = client.post("/users/login", json={"email": "normal@example.com", "password": "123456"}).json()["access_token"]

    response = client.patch(
        f"/users/{user.id_usuario}/password",
        json={"new_password": "clave-nueva-123"},
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_openapi_schema_builds(client):
    """La documentación (/docs) se genera sin errores de esquemas."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "google_conectado" in response.json()["components"]["schemas"]["UserResponse"]["properties"]

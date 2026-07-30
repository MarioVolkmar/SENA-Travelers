from app.models.user_model import UserModel
from app.core.constants import EMAIL_VERIFICATION_VERIFIED


def test_unverified_user_cannot_login(client):
    client.post(
        "/users/",
        json={
            "nombre": "Usuario No Verificado",
            "email": "no_verificado@example.com",
            "password": "123456"
        }
    )

    response = client.post(
        "/users/login",
        json={
            "email": "no_verificado@example.com",
            "password": "123456"
        }
    )

    assert response.status_code == 401


def test_verified_user_can_login(client, db_session):
    client.post(
        "/users/",
        json={
            "nombre": "Usuario Verificado",
            "email": "verificado@example.com",
            "password": "123456"
        }
    )

    user = (
        db_session.query(UserModel)
        .filter(UserModel.email == "verificado@example.com")
        .first()
    )

    user.verificacion_email = EMAIL_VERIFICATION_VERIFIED
    db_session.commit()

    response = client.post(
        "/users/login",
        json={
            "email": "verificado@example.com",
            "password": "123456"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"


def test_users_me_without_token_returns_401(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_users_me_with_invalid_token_returns_401(client):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer token_invalido"
        }
    )

    assert response.status_code == 401


def test_users_me_with_valid_token_returns_200(client, db_session):
    client.post(
        "/users/",
        json={
            "nombre": "Usuario Token",
            "email": "token_user@example.com",
            "password": "123456"
        }
    )

    user = (
        db_session.query(UserModel)
        .filter(UserModel.email == "token_user@example.com")
        .first()
    )

    user.verificacion_email = EMAIL_VERIFICATION_VERIFIED
    db_session.commit()

    login_response = client.post(
        "/users/login",
        json={
            "email": "token_user@example.com",
            "password": "123456"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "token_user@example.com"
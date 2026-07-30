from app.models.user_model import UserModel
from app.core.constants import (
    ADMIN_ROLE_ID,
    CLIENT_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED
)

def verify_user_email(db_session, email: str):
    db_session.rollback()
    db_session.expire_all()

    user = (
        db_session.query(UserModel)
        .filter(UserModel.email == email)
        .first()
    )

    assert user is not None

    user.verificacion_email = EMAIL_VERIFICATION_VERIFIED
    db_session.commit()
    db_session.refresh(user)

    return user

def create_verified_user(
    client,
    db_session,
    nombre: str,
    email: str,
    password: str = "123456"
):
    response = client.post(
        "/users/",
        json={
            "nombre": nombre,
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 201, response.json()

    return verify_user_email(db_session, email)

def login_user(client, email: str, password: str = "123456"):
    response = client.post(
        "/users/login",
        json={
            "email": email,
            "password": password
        }
    )

    return response.json()["access_token"]


def test_client_cannot_list_users(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Normal",
        email="cliente_normal@example.com"
    )

    token = login_user(client, "cliente_normal@example.com")

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_list_users(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Test",
        email="admin_test@example.com"
    )

    admin.rol_id = ADMIN_ROLE_ID
    db_session.commit()

    token = login_user(client, "admin_test@example.com")

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_client_cannot_update_user_role(client, db_session):
    client_user = create_verified_user(
        client,
        db_session,
        nombre="Cliente Sin Permiso",
        email="cliente_sin_permiso@example.com"
    )

    target_user = create_verified_user(
        client,
        db_session,
        nombre="Usuario Objetivo",
        email="usuario_objetivo@example.com"
    )

    token = login_user(client, "cliente_sin_permiso@example.com")

    response = client.patch(
        f"/users/{target_user.id_usuario}/role",
        json={
            "rol_id": ADMIN_ROLE_ID
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_update_user_role(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Cambio Rol",
        email="admin_cambio_rol@example.com"
    )

    admin.rol_id = ADMIN_ROLE_ID
    db_session.commit()

    target_user = create_verified_user(
        client,
        db_session,
        nombre="Usuario Cambio Rol",
        email="usuario_cambio_rol@example.com"
    )

    token = login_user(client, "admin_cambio_rol@example.com")

    response = client.patch(
        f"/users/{target_user.id_usuario}/role",
        json={
            "rol_id": CLIENT_ROLE_ID
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
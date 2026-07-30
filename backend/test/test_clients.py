from app.models.user_model import UserModel
from app.core.constants import EMAIL_VERIFICATION_VERIFIED, ADMIN_ROLE_ID

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


def create_user(
    client,
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

    return response.json()


def login_user(client, email: str, password: str = "123456"):
    response = client.post(
        "/users/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200, response.json()

    return response.json()["access_token"]


def create_verified_user(
    client,
    db_session,
    nombre: str,
    email: str,
    password: str = "123456"
):
    create_user(client, nombre, email, password)
    return verify_user_email(db_session, email)


def test_verified_user_can_create_client_profile(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Test",
        email="cliente_test@example.com"
    )

    token = login_user(client, "cliente_test@example.com")

    response = client.post(
        "/clients/me",
        json={
            "identificacion": "123456789",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201


def test_user_without_token_cannot_create_client_profile(client):
    response = client.post(
        "/clients/me",
        json={
            "identificacion": "987654321",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        }
    )

    assert response.status_code == 401


def test_unverified_user_cannot_create_client_profile(client):
    create_user(
        client,
        nombre="Cliente No Verificado",
        email="cliente_no_verificado@example.com"
    )

    # No puede hacer login si no está verificado.
    login_response = client.post(
        "/users/login",
        json={
            "email": "cliente_no_verificado@example.com",
            "password": "123456"
        }
    )

    assert login_response.status_code == 401

def test_user_cannot_create_two_client_profiles(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Duplicado",
        email="cliente_duplicado@example.com"
    )

    token = login_user(client, "cliente_duplicado@example.com")

    client.post(
        "/clients/me",
        json={
            "identificacion": "111222333",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    response = client.post(
        "/clients/me",
        json={
            "identificacion": "444555666",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400


def test_client_can_get_own_profile(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Perfil",
        email="cliente_perfil@example.com"
    )

    token = login_user(client, "cliente_perfil@example.com")

    client.post(
        "/clients/me",
        json={
            "identificacion": "555666777",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    response = client.get(
        "/clients/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["identificacion"] == "555666777"
    assert data["ciudad_id"] == 1


def test_create_client_profile_with_invalid_city_returns_400(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Ciudad Invalida",
        email="cliente_ciudad_invalida@example.com"
    )

    token = login_user(client, "cliente_ciudad_invalida@example.com")

    response = client.post(
        "/clients/me",
        json={
            "identificacion": "999888777",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 999
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400

def test_admin_can_list_clients(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Clientes",
        email="admin_clientes@example.com"
    )

    admin.rol_id = ADMIN_ROLE_ID
    db_session.commit()

    user = create_verified_user(
        client,
        db_session,
        nombre="Cliente Lista",
        email="cliente_lista@example.com"
    )

    client_token = login_user(client, "cliente_lista@example.com")

    client.post(
        "/clients/me",
        json={
            "identificacion": "101010101",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    admin_token = login_user(client, "admin_clientes@example.com")

    response = client.get(
        "/clients/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_normal_client_cannot_list_clients(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Sin Permiso Lista",
        email="cliente_sin_permiso_lista@example.com"
    )

    token = login_user(client, "cliente_sin_permiso_lista@example.com")

    response = client.get(
        "/clients/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_get_client_by_id(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Consulta Cliente",
        email="admin_consulta_cliente@example.com"
    )

    admin.rol_id = ADMIN_ROLE_ID
    db_session.commit()

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Consultado",
        email="cliente_consultado@example.com"
    )

    client_token = login_user(client, "cliente_consultado@example.com")

    create_response = client.post(
        "/clients/me",
        json={
            "identificacion": "202020202",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    id_cliente = create_response.json()["id_cliente"]

    admin_token = login_user(client, "admin_consulta_cliente@example.com")

    response = client.get(
        f"/clients/{id_cliente}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200


def test_normal_client_cannot_get_client_by_id(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Dueño",
        email="cliente_dueno@example.com"
    )

    owner_token = login_user(client, "cliente_dueno@example.com")

    create_response = client.post(
        "/clients/me",
        json={
            "identificacion": "303030303",
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {owner_token}"
        }
    )

    id_cliente = create_response.json()["id_cliente"]

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Otro",
        email="cliente_otro@example.com"
    )

    other_token = login_user(client, "cliente_otro@example.com")

    response = client.get(
        f"/clients/{id_cliente}",
        headers={
            "Authorization": f"Bearer {other_token}"
        }
    )

    assert response.status_code == 403
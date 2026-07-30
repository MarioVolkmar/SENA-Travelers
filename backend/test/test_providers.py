from app.models.user_model import UserModel
from app.models.provider_model import ProviderModel

from app.core.constants import (
    ADMIN_ROLE_ID,
    PROVIDER_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED,
    PROVIDER_STATUS_APPROVED,
    PROVIDER_STATUS_PENDING,
    CLIENT_ROLE_ID, 
    PROVIDER_STATUS_REJECTED
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


def make_user_admin(db_session, user: UserModel):
    user.rol_id = ADMIN_ROLE_ID
    db_session.commit()
    db_session.refresh(user)
    return user


def create_provider_profile(
    client,
    token: str,
    rut: str = "900123456",
    telefono: str = "3001234567",
    direccion: str = "Calle 10 # 20-30",
    nombre_empresa: str = "Travel Provider Test",
    ciudad_id: int = 1
):
    return client.post(
        "/providers/me",
        json={
            "rut": rut,
            "telefono": telefono,
            "direccion": direccion,
            "nombre_empresa": nombre_empresa,
            "ciudad_id": ciudad_id
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

def test_verified_user_can_create_provider_request(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Solicitante",
        email="proveedor_solicitante@example.com"
    )

    token = login_user(client, "proveedor_solicitante@example.com")

    response = create_provider_profile(
        client,
        token,
        rut="900111222",
        nombre_empresa="Agencia Test"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["rut"] == "900111222"
    assert data["nombre_empresa"] == "Agencia Test"
    assert data["estado_verificacion"] == PROVIDER_STATUS_PENDING


def test_user_without_token_cannot_create_provider_request(client):
    response = client.post(
        "/providers/me",
        json={
            "rut": "900333444",
            "telefono": "3001234567",
            "direccion": "Calle 10 # 20-30",
            "nombre_empresa": "Proveedor Sin Token",
            "ciudad_id": 1
        }
    )

    assert response.status_code == 401


def test_unverified_user_cannot_create_provider_request(client):
    create_user(
        client,
        nombre="Proveedor No Verificado",
        email="proveedor_no_verificado@example.com"
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "proveedor_no_verificado@example.com",
            "password": "123456"
        }
    )

    assert login_response.status_code == 401


def test_user_cannot_create_two_provider_profiles(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Duplicado",
        email="proveedor_duplicado@example.com"
    )

    token = login_user(client, "proveedor_duplicado@example.com")

    first_response = create_provider_profile(
        client,
        token,
        rut="900555666",
        nombre_empresa="Proveedor Uno"
    )

    assert first_response.status_code == 201

    second_response = create_provider_profile(
        client,
        token,
        rut="900777888",
        nombre_empresa="Proveedor Dos"
    )

    assert second_response.status_code == 400


def test_create_provider_with_invalid_city_returns_400(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Ciudad Invalida",
        email="proveedor_ciudad_invalida@example.com"
    )

    token = login_user(client, "proveedor_ciudad_invalida@example.com")

    response = create_provider_profile(
        client,
        token,
        rut="900999000",
        nombre_empresa="Proveedor Ciudad Invalida",
        ciudad_id=999
    )

    assert response.status_code == 400

def test_admin_can_list_pending_providers(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Pendientes",
        email="admin_pendientes@example.com"
    )
    make_user_admin(db_session, admin)

    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Pendiente",
        email="proveedor_pendiente@example.com"
    )

    provider_token = login_user(client, "proveedor_pendiente@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="901111222",
        nombre_empresa="Proveedor Pendiente"
    )

    assert create_response.status_code == 201

    admin_token = login_user(client, "admin_pendientes@example.com")

    response = client.get(
        "/providers/pending",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_normal_user_cannot_list_pending_providers(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Usuario Sin Permiso Pending",
        email="usuario_sin_permiso_pending@example.com"
    )

    token = login_user(client, "usuario_sin_permiso_pending@example.com")

    response = client.get(
        "/providers/pending",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_approve_provider_and_user_role_changes(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Aprueba",
        email="admin_aprueba@example.com"
    )
    make_user_admin(db_session, admin)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Para Aprobar",
        email="proveedor_para_aprobar@example.com"
    )

    provider_token = login_user(client, "proveedor_para_aprobar@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="902222333",
        nombre_empresa="Proveedor Para Aprobar"
    )

    assert create_response.status_code == 201

    id_proveedor = create_response.json()["id_proveedor"]

    admin_token = login_user(client, "admin_aprueba@example.com")

    response = client.patch(
        f"/providers/{id_proveedor}/verification-status",
        json={
            "estado_verificacion": PROVIDER_STATUS_APPROVED
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    db_session.rollback()
    db_session.expire_all()

    updated_user = (
        db_session.query(UserModel)
        .filter(UserModel.id_usuario == provider_user.id_usuario)
        .first()
    )

    assert updated_user.rol_id == PROVIDER_ROLE_ID


def test_normal_user_cannot_approve_provider(client, db_session):
    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor No Admin",
        email="proveedor_no_admin@example.com"
    )

    provider_token = login_user(client, "proveedor_no_admin@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="903333444",
        nombre_empresa="Proveedor No Admin"
    )

    assert create_response.status_code == 201

    id_proveedor = create_response.json()["id_proveedor"]

    normal_user = create_verified_user(
        client,
        db_session,
        nombre="Usuario Normal Aprueba",
        email="usuario_normal_aprueba@example.com"
    )

    normal_token = login_user(client, "usuario_normal_aprueba@example.com")

    response = client.patch(
        f"/providers/{id_proveedor}/verification-status",
        json={
            "estado_verificacion": PROVIDER_STATUS_APPROVED
        },
        headers={
            "Authorization": f"Bearer {normal_token}"
        }
    )

    assert response.status_code == 403


def test_admin_cannot_set_provider_status_to_pending(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Pending Invalido",
        email="admin_pending_invalido@example.com"
    )
    make_user_admin(db_session, admin)

    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Pending Invalido",
        email="proveedor_pending_invalido@example.com"
    )

    provider_token = login_user(client, "proveedor_pending_invalido@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="904444555",
        nombre_empresa="Proveedor Pending Invalido"
    )

    assert create_response.status_code == 201

    id_proveedor = create_response.json()["id_proveedor"]

    admin_token = login_user(client, "admin_pending_invalido@example.com")

    response = client.patch(
        f"/providers/{id_proveedor}/verification-status",
        json={
            "estado_verificacion": PROVIDER_STATUS_PENDING
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 400

def test_admin_can_reject_provider_and_user_role_becomes_client(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Rechaza",
        email="admin_rechaza@example.com"
    )
    make_user_admin(db_session, admin)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Para Rechazar",
        email="proveedor_para_rechazar@example.com"
    )

    provider_token = login_user(client, "proveedor_para_rechazar@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="905555666",
        nombre_empresa="Proveedor Para Rechazar"
    )

    assert create_response.status_code == 201

    id_proveedor = create_response.json()["id_proveedor"]

    admin_token = login_user(client, "admin_rechaza@example.com")

    response = client.patch(
        f"/providers/{id_proveedor}/verification-status",
        json={
            "estado_verificacion": PROVIDER_STATUS_REJECTED
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    db_session.rollback()
    db_session.expire_all()

    updated_user = (
        db_session.query(UserModel)
        .filter(UserModel.id_usuario == provider_user.id_usuario)
        .first()
    )

    assert updated_user.rol_id == CLIENT_ROLE_ID


def test_provider_can_get_own_profile(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Perfil Propio",
        email="proveedor_perfil_propio@example.com"
    )

    token = login_user(client, "proveedor_perfil_propio@example.com")

    create_response = create_provider_profile(
        client,
        token,
        rut="906666777",
        nombre_empresa="Proveedor Perfil Propio"
    )

    assert create_response.status_code == 201

    response = client.get(
        "/providers/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["rut"] == "906666777"
    assert data["nombre_empresa"] == "Proveedor Perfil Propio"


def test_admin_can_get_provider_by_id(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Consulta Proveedor",
        email="admin_consulta_proveedor@example.com"
    )
    make_user_admin(db_session, admin)

    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Consultado",
        email="proveedor_consultado@example.com"
    )

    provider_token = login_user(client, "proveedor_consultado@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="907777888",
        nombre_empresa="Proveedor Consultado"
    )

    assert create_response.status_code == 201

    id_proveedor = create_response.json()["id_proveedor"]

    admin_token = login_user(client, "admin_consulta_proveedor@example.com")

    response = client.get(
        f"/providers/{id_proveedor}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200


def test_normal_user_cannot_get_provider_by_id(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Privado",
        email="proveedor_privado@example.com"
    )

    provider_token = login_user(client, "proveedor_privado@example.com")

    create_response = create_provider_profile(
        client,
        provider_token,
        rut="908888999",
        nombre_empresa="Proveedor Privado"
    )

    assert create_response.status_code == 201

    id_proveedor = create_response.json()["id_proveedor"]

    create_verified_user(
        client,
        db_session,
        nombre="Usuario Consulta Sin Permiso",
        email="usuario_consulta_sin_permiso@example.com"
    )

    normal_token = login_user(client, "usuario_consulta_sin_permiso@example.com")

    response = client.get(
        f"/providers/{id_proveedor}",
        headers={
            "Authorization": f"Bearer {normal_token}"
        }
    )

    assert response.status_code == 403
from app.models.user_model import UserModel

from app.core.constants import (
    ADMIN_ROLE_ID,
    PROVIDER_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED,
    PROVIDER_STATUS_APPROVED,
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
    rut: str,
    nombre_empresa: str,
    ciudad_id: int = 1
):
    response = client.post(
        "/providers/me",
        json={
            "rut": rut,
            "telefono": "3001234567",
            "direccion": "Calle 10 # 20-30",
            "nombre_empresa": nombre_empresa,
            "ciudad_id": ciudad_id
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201, response.json()
    return response.json()


def approve_provider(client, admin_token: str, id_proveedor: int):
    response = client.patch(
        f"/providers/{id_proveedor}/verification-status",
        json={
            "estado_verificacion": PROVIDER_STATUS_APPROVED
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200, response.json()
    return response.json()


def create_product(
    client,
    token: str,
    proveedor_id: int,
    nombre: str = "Tour Producto Test",
    ciudad_id: int = 1
):
    return client.post(
        "/products/",
        json={
            "nombre": nombre,
            "descripcion": "Producto turístico de prueba con descripción suficiente",
            "tipo_producto": "tour",
            "costo": "150000.00",
            "ciudad_id": ciudad_id,
            "proveedor_id": proveedor_id
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

def test_admin_can_create_product(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Producto",
        email="admin_producto@example.com"
    )
    make_user_admin(db_session, admin)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Producto Admin",
        email="proveedor_producto_admin@example.com"
    )

    provider_token = login_user(client, "proveedor_producto_admin@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="909111222",
        nombre_empresa="Proveedor Producto Admin"
    )

    admin_token = login_user(client, "admin_producto@example.com")

    approve_provider(
        client,
        admin_token,
        provider["id_proveedor"]
    )

    response = create_product(
        client,
        admin_token,
        proveedor_id=provider["id_proveedor"],
        nombre="Producto Creado Por Admin"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["nombre"] == "Producto Creado Por Admin"
    assert data["proveedor_id"] == provider["id_proveedor"]


def test_approved_provider_can_create_own_product(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Aprueba Producto",
        email="admin_aprueba_producto@example.com"
    )
    make_user_admin(db_session, admin)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Crea Producto",
        email="proveedor_crea_producto@example.com"
    )

    provider_token = login_user(client, "proveedor_crea_producto@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="909333444",
        nombre_empresa="Proveedor Crea Producto"
    )

    admin_token = login_user(client, "admin_aprueba_producto@example.com")

    approve_provider(
        client,
        admin_token,
        provider["id_proveedor"]
    )

    # Después de aprobar, volvemos a hacer login para obtener token actualizado
    provider_token = login_user(client, "proveedor_crea_producto@example.com")

    response = create_product(
        client,
        provider_token,
        proveedor_id=provider["id_proveedor"],
        nombre="Producto Del Proveedor"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["nombre"] == "Producto Del Proveedor"
    assert data["proveedor_id"] == provider["id_proveedor"]


def test_normal_user_cannot_create_product(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Producto Bloqueado",
        email="admin_producto_bloqueado@example.com"
    )
    make_user_admin(db_session, admin)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Producto Bloqueado",
        email="proveedor_producto_bloqueado@example.com"
    )

    provider_token = login_user(client, "proveedor_producto_bloqueado@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="909999111",
        nombre_empresa="Proveedor Producto Bloqueado"
    )

    admin_token = login_user(client, "admin_producto_bloqueado@example.com")

    approve_provider(
        client,
        admin_token,
        provider["id_proveedor"]
    )

    create_verified_user(
        client,
        db_session,
        nombre="Usuario No Producto",
        email="usuario_no_producto@example.com"
    )

    normal_user_token = login_user(client, "usuario_no_producto@example.com")

    response = create_product(
        client,
        normal_user_token,
        proveedor_id=provider["id_proveedor"],
        nombre="Producto No Permitido"
    )

    assert response.status_code == 403


def test_pending_provider_cannot_create_product(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Pendiente Producto",
        email="proveedor_pendiente_producto@example.com"
    )

    provider_token = login_user(client, "proveedor_pendiente_producto@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="909555666",
        nombre_empresa="Proveedor Pendiente Producto"
    )

    response = create_product(
        client,
        provider_token,
        proveedor_id=provider["id_proveedor"],
        nombre="Producto Pendiente"
    )

    assert response.status_code == 403


def test_public_can_list_active_products(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Lista Productos",
        email="admin_lista_productos@example.com"
    )
    make_user_admin(db_session, admin)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Lista Productos",
        email="proveedor_lista_productos@example.com"
    )

    provider_token = login_user(client, "proveedor_lista_productos@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="909777888",
        nombre_empresa="Proveedor Lista Productos"
    )

    admin_token = login_user(client, "admin_lista_productos@example.com")

    approve_provider(
        client,
        admin_token,
        provider["id_proveedor"]
    )

    create_response = create_product(
        client,
        admin_token,
        proveedor_id=provider["id_proveedor"],
        nombre="Producto Publico Activo"
    )

    assert create_response.status_code == 201

    response = client.get("/products/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
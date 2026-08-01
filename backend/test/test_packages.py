from app.models.user_model import UserModel

from app.core.constants import (
    ADMIN_ROLE_ID,
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
    nombre: str = "Producto Para Paquete",
    ciudad_id: int = 1
):
    response = client.post(
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

    assert response.status_code == 201, response.json()
    return response.json()


def create_admin_with_token(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Paquetes",
        email="admin_paquetes@example.com"
    )

    make_user_admin(db_session, admin)

    admin_token = login_user(client, "admin_paquetes@example.com")

    return admin, admin_token


def create_approved_provider_with_product(
    client,
    db_session,
    admin_token: str,
    provider_email: str = "proveedor_paquete@example.com",
    rut: str = "910111222",
    product_name: str = "Producto Base Paquete"
):
    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Paquete",
        email=provider_email
    )

    provider_token = login_user(client, provider_email)

    provider = create_provider_profile(
        client,
        provider_token,
        rut=rut,
        nombre_empresa="Proveedor Paquete"
    )

    approve_provider(
        client,
        admin_token,
        provider["id_proveedor"]
    )

    product = create_product(
        client,
        admin_token,
        proveedor_id=provider["id_proveedor"],
        nombre=product_name
    )

    return provider, product


def create_package(
    client,
    token: str,
    producto_id: int,
    nombre: str = "Paquete Guatapé Test",
    ciudad_id: int = 1,
    fecha_inicio: str = "2026-09-10",
    fecha_fin: str = "2026-09-12"
):
    return client.post(
        "/packages/",
        json={
            "nombre": nombre,
            "descripcion": "Paquete turístico de prueba con varios servicios incluidos.",
            "precio": "650000.00",
            "descuento": 0,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "cupo_max": 20,
            "ciudad_id": ciudad_id,
            "productos": [
                {
                    "producto_id": producto_id,
                    "cantidad": 1
                }
            ]
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

def test_admin_can_create_package_with_active_product(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_create@example.com",
        rut="910222333",
        product_name="Producto Para Crear Paquete"
    )

    response = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Creado Por Admin"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["nombre"] == "Paquete Creado Por Admin"
    assert data["ciudad_id"] == 1
    assert data["estado"] == "activo"


def test_normal_user_cannot_create_package(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_no_permiso@example.com",
        rut="910333444",
        product_name="Producto Paquete Sin Permiso"
    )

    create_verified_user(
        client,
        db_session,
        nombre="Usuario Normal Paquete",
        email="usuario_normal_paquete@example.com"
    )

    normal_token = login_user(client, "usuario_normal_paquete@example.com")

    response = create_package(
        client,
        normal_token,
        producto_id=product["id_producto"],
        nombre="Paquete No Permitido"
    )

    assert response.status_code == 403


def test_create_package_with_invalid_city_returns_400(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_ciudad@example.com",
        rut="910444555",
        product_name="Producto Paquete Ciudad"
    )

    response = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Ciudad Invalida",
        ciudad_id=999
    )

    assert response.status_code == 400


def test_create_package_with_invalid_dates_returns_400(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_fechas@example.com",
        rut="910555666",
        product_name="Producto Paquete Fechas"
    )

    response = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Fechas Invalidas",
        fecha_inicio="2026-09-12",
        fecha_fin="2026-09-10"
    )

    assert response.status_code == 400


def test_create_package_with_nonexistent_product_returns_400(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    response = create_package(
        client,
        admin_token,
        producto_id=999,
        nombre="Paquete Producto Inexistente"
    )

    assert response.status_code == 400


def test_public_can_list_active_packages(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_lista@example.com",
        rut="910666777",
        product_name="Producto Paquete Lista"
    )

    create_response = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Publico Activo"
    )

    assert create_response.status_code == 201

    response = client.get("/packages/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_admin_can_list_all_packages(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    response = client.get(
        "/packages/admin",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_normal_user_cannot_list_all_packages_admin(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Usuario No Admin Packages",
        email="usuario_no_admin_packages@example.com"
    )

    token = login_user(client, "usuario_no_admin_packages@example.com")

    response = client.get(
        "/packages/admin",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_deactivate_package(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_inactivar@example.com",
        rut="910777888",
        product_name="Producto Paquete Inactivar"
    )

    create_response = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Para Inactivar"
    )

    assert create_response.status_code == 201

    id_paquete = create_response.json()["id_paquete_turistico"]

    response = client.patch(
        f"/packages/{id_paquete}/status",
        json={
            "estado": "inactivo"
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "inactivo"


def test_inactive_package_is_not_available_publicly(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider, product = create_approved_provider_with_product(
        client,
        db_session,
        admin_token,
        provider_email="proveedor_paquete_no_publico@example.com",
        rut="910888999",
        product_name="Producto Paquete No Publico"
    )

    create_response = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete No Publico"
    )

    assert create_response.status_code == 201

    id_paquete = create_response.json()["id_paquete_turistico"]

    deactivate_response = client.patch(
        f"/packages/{id_paquete}/status",
        json={
            "estado": "inactivo"
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert deactivate_response.status_code == 200

    response = client.get(f"/packages/{id_paquete}")

    assert response.status_code == 404
from app.models.user_model import UserModel

from app.core.constants import (
    ADMIN_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED,
    PROVIDER_STATUS_APPROVED,
    RESERVATION_STATUS_CONFIRMED
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


def create_admin_with_token(client, db_session):
    admin = create_verified_user(
        client,
        db_session,
        nombre="Admin Reservas",
        email="admin_reservas@example.com"
    )

    make_user_admin(db_session, admin)

    admin_token = login_user(client, "admin_reservas@example.com")

    return admin, admin_token


def create_client_profile(client, token: str, identificacion: str = "123456789"):
    response = client.post(
        "/clients/me",
        json={
            "identificacion": identificacion,
            "fecha_nacimiento": "1994-05-20",
            "ciudad_id": 1
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201, response.json()
    return response.json()


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
    nombre: str = "Producto Para Reserva",
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


def create_package(
    client,
    token: str,
    producto_id: int,
    nombre: str = "Paquete Para Reserva",
    ciudad_id: int = 1,
    fecha_inicio: str = "2026-09-10",
    fecha_fin: str = "2026-09-12"
):
    response = client.post(
        "/packages/",
        json={
            "nombre": nombre,
            "descripcion": "Paquete turístico de prueba para reservas.",
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

    assert response.status_code == 201, response.json()
    return response.json()


def create_package_ready_for_reservation(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    provider_user = create_verified_user(
        client,
        db_session,
        nombre="Proveedor Reserva",
        email="proveedor_reserva@example.com"
    )

    provider_token = login_user(client, "proveedor_reserva@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="920111222",
        nombre_empresa="Proveedor Reserva"
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
        nombre="Producto Reserva"
    )

    package = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Reserva"
    )

    return package, admin_token


def create_reservation(
    client,
    token: str,
    id_paquete_turistico: int,
    fecha_reserva: str = "2026-09-10",
    cantidad_personas: int = 2,
    acompanantes=None
):
    if acompanantes is None:
        acompanantes = [
            {
                "nombre": "Acompañante Test",
                "documento": "987654321",
                "fecha_nacimiento": "1995-04-15"
            }
        ]

    return client.post(
        "/reservations/",
        json={
            "id_paquete_turistico": id_paquete_turistico,
            "fecha_reserva": fecha_reserva,
            "cantidad_personas": cantidad_personas,
            "acompanantes": acompanantes
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

def test_client_can_create_reservation_with_companion(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Reserva",
        email="cliente_reserva@example.com"
    )

    client_token = login_user(client, "cliente_reserva@example.com")

    create_client_profile(
        client,
        client_token,
        identificacion="111222333"
    )

    response = create_reservation(
        client,
        client_token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id_paquete_turistico"] == package["id_paquete_turistico"]
    assert data["cantidad_personas"] == 2
    assert data["estado"] == "pendiente"
    assert "codigo_reserva" in data
    assert "total_reserva" in data


def test_user_without_client_profile_cannot_create_reservation(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Usuario Sin Perfil Cliente",
        email="usuario_sin_perfil_cliente@example.com"
    )

    token = login_user(client, "usuario_sin_perfil_cliente@example.com")

    response = create_reservation(
        client,
        token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert response.status_code == 403


def test_create_reservation_with_nonexistent_package_returns_404(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Paquete Inexistente",
        email="cliente_paquete_inexistente@example.com"
    )

    token = login_user(client, "cliente_paquete_inexistente@example.com")

    create_client_profile(
        client,
        token,
        identificacion="222333444"
    )

    response = create_reservation(
        client,
        token,
        id_paquete_turistico=999
    )

    assert response.status_code == 404


def test_create_reservation_with_date_before_package_start_returns_400(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Fecha Antes",
        email="cliente_fecha_antes@example.com"
    )

    token = login_user(client, "cliente_fecha_antes@example.com")

    create_client_profile(
        client,
        token,
        identificacion="333444555"
    )

    response = create_reservation(
        client,
        token,
        id_paquete_turistico=package["id_paquete_turistico"],
        fecha_reserva="2026-09-09"
    )

    assert response.status_code == 400


def test_create_reservation_with_date_after_package_end_returns_400(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Fecha Despues",
        email="cliente_fecha_despues@example.com"
    )

    token = login_user(client, "cliente_fecha_despues@example.com")

    create_client_profile(
        client,
        token,
        identificacion="444555666"
    )

    response = create_reservation(
        client,
        token,
        id_paquete_turistico=package["id_paquete_turistico"],
        fecha_reserva="2026-09-13"
    )

    assert response.status_code == 400


def test_create_reservation_with_too_many_companions_returns_400(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Muchos Acompanantes",
        email="cliente_muchos_acompanantes@example.com"
    )

    token = login_user(client, "cliente_muchos_acompanantes@example.com")

    create_client_profile(
        client,
        token,
        identificacion="555666777"
    )

    response = create_reservation(
        client,
        token,
        id_paquete_turistico=package["id_paquete_turistico"],
        cantidad_personas=2,
        acompanantes=[
            {
                "nombre": "Acompañante Uno",
                "documento": "100000001",
                "fecha_nacimiento": "1995-04-15"
            },
            {
                "nombre": "Acompañante Dos",
                "documento": "100000002",
                "fecha_nacimiento": "1996-04-15"
            }
        ]
    )

    assert response.status_code == 400


def test_client_can_list_own_reservations(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Mis Reservas",
        email="cliente_mis_reservas@example.com"
    )

    token = login_user(client, "cliente_mis_reservas@example.com")

    create_client_profile(
        client,
        token,
        identificacion="666777888"
    )

    create_response = create_reservation(
        client,
        token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert create_response.status_code == 201

    response = client.get(
        "/reservations/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_admin_can_list_all_reservations(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Reserva Admin Lista",
        email="cliente_reserva_admin_lista@example.com"
    )

    client_token = login_user(client, "cliente_reserva_admin_lista@example.com")

    create_client_profile(
        client,
        client_token,
        identificacion="777888999"
    )

    create_response = create_reservation(
        client,
        client_token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert create_response.status_code == 201

    response = client.get(
        "/reservations/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_normal_client_cannot_list_all_reservations(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente No Admin Reservas",
        email="cliente_no_admin_reservas@example.com"
    )

    token = login_user(client, "cliente_no_admin_reservas@example.com")

    create_client_profile(
        client,
        token,
        identificacion="888999000"
    )

    response = client.get(
        "/reservations/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

def test_client_can_get_own_reservation_by_id(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Consulta Reserva Propia",
        email="cliente_consulta_reserva_propia@example.com"
    )

    token = login_user(client, "cliente_consulta_reserva_propia@example.com")

    create_client_profile(
        client,
        token,
        identificacion="901901901"
    )

    create_response = create_reservation(
        client,
        token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert create_response.status_code == 201

    id_reserva = create_response.json()["id_reserva"]

    response = client.get(
        f"/reservations/{id_reserva}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200


def test_client_cannot_get_other_client_reservation(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Dueño Reserva",
        email="cliente_dueno_reserva@example.com"
    )

    owner_token = login_user(client, "cliente_dueno_reserva@example.com")

    create_client_profile(
        client,
        owner_token,
        identificacion="902902902"
    )

    create_response = create_reservation(
        client,
        owner_token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert create_response.status_code == 201

    id_reserva = create_response.json()["id_reserva"]

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Otro Reserva",
        email="cliente_otro_reserva@example.com"
    )

    other_token = login_user(client, "cliente_otro_reserva@example.com")

    create_client_profile(
        client,
        other_token,
        identificacion="903903903"
    )

    response = client.get(
        f"/reservations/{id_reserva}",
        headers={
            "Authorization": f"Bearer {other_token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_update_reservation_status(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    create_verified_user(
        client,
        db_session,
        nombre="Cliente Reserva Cambio Estado",
        email="cliente_reserva_cambio_estado@example.com"
    )

    client_token = login_user(client, "cliente_reserva_cambio_estado@example.com")

    create_client_profile(
        client,
        client_token,
        identificacion="904904904"
    )

    create_response = create_reservation(
        client,
        client_token,
        id_paquete_turistico=package["id_paquete_turistico"]
    )

    assert create_response.status_code == 201

    id_reserva = create_response.json()["id_reserva"]

    response = client.patch(
        f"/reservations/{id_reserva}/status",
        json={
            "estado": RESERVATION_STATUS_CONFIRMED
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["estado"] == RESERVATION_STATUS_CONFIRMED
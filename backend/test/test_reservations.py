from app.models.user_model import UserModel
from app.models.reservation_model import ReservationModel
from app.models.notification_email_model import NotificationEmailModel

from app.core.constants import (
    ADMIN_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED,
    PROVIDER_STATUS_APPROVED,
    RESERVATION_STATUS_CONFIRMED,
    NOTIFICATION_TYPE_RESERVATION_CONFIRMATION,
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


def create_client_profile(client, token: str, identificacion: str):
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
    nombre_empresa: str
):
    response = client.post(
        "/providers/me",
        json={
            "rut": rut,
            "telefono": "3001234567",
            "direccion": "Calle 10 # 20-30",
            "nombre_empresa": nombre_empresa,
            "ciudad_id": 1
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
    nombre: str = "Producto Para Reserva"
):
    response = client.post(
        "/products/",
        json={
            "nombre": nombre,
            "descripcion": "Producto turístico de prueba con descripción suficiente",
            "tipo_producto": "tour",
            "costo": "150000.00",
            "ciudad_id": 1,
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
    nombre: str = "Paquete Para Reserva"
):
    response = client.post(
        "/packages/",
        json={
            "nombre": nombre,
            "descripcion": "Paquete turístico de prueba para reservas.",
            "precio": "650000.00",
            "descuento": 0,
            "fecha_inicio": "2026-09-10",
            "fecha_fin": "2026-09-12",
            "cupo_max": 20,
            "ciudad_id": 1,
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

    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Reserva",
        email="proveedor_reserva@example.com"
    )

    provider_token = login_user(client, "proveedor_reserva@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="910111222",
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


def create_client_with_token(
    client,
    db_session,
    email: str,
    identificacion: str,
    nombre: str = "Cliente Reserva"
):
    create_verified_user(
        client,
        db_session,
        nombre=nombre,
        email=email
    )

    client_token = login_user(client, email)

    client_profile = create_client_profile(
        client,
        client_token,
        identificacion=identificacion
    )

    return client_token, client_profile


def create_reservation(
    client,
    token: str,
    package_id: int,
    fecha_reserva: str = "2026-09-10",
    cantidad_personas: int = 2,
    acompanantes=None
):
    if acompanantes is None:
        acompanantes = [
            {
                "nombre": "Acompañante Reserva",
                "documento": "123123123",
                "fecha_nacimiento": "1995-04-15"
            }
        ]

    return client.post(
        "/reservations/",
        json={
            "id_paquete_turistico": package_id,
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

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_reserva@example.com",
        identificacion="100100100"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"]
    )

    assert response.status_code == 201, response.json()

    data = response.json()

    assert data["id_paquete_turistico"] == package["id_paquete_turistico"]
    assert data["cliente_id"] == client_profile["id_cliente"]
    assert data["cantidad_personas"] == 2
    assert data["estado"] == "pendiente"
    assert data["total_reserva"] == "1300000.00"
    assert "codigo_reserva" in data


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
        package_id=package["id_paquete_turistico"]
    )

    assert response.status_code == 403


def test_cannot_create_reservation_with_nonexistent_package(client, db_session):
    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_paquete_inexistente@example.com",
        identificacion="200200200"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=999
    )

    assert response.status_code == 404


def test_cannot_create_reservation_before_package_start_date(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_fecha_antes@example.com",
        identificacion="300300300"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"],
        fecha_reserva="2026-09-09"
    )

    assert response.status_code == 400


def test_cannot_create_reservation_after_package_end_date(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_fecha_despues@example.com",
        identificacion="400400400"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"],
        fecha_reserva="2026-09-13"
    )

    assert response.status_code == 400


def test_cannot_create_reservation_with_too_many_companions(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_muchos_acompanantes@example.com",
        identificacion="500500500"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"],
        cantidad_personas=2,
        acompanantes=[
            {
                "nombre": "Acompañante Uno",
                "documento": "111111111",
                "fecha_nacimiento": "1995-04-15"
            },
            {
                "nombre": "Acompañante Dos",
                "documento": "222222222",
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

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_lista_reservas@example.com",
        identificacion="600600600"
    )

    reservation_response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"]
    )

    assert reservation_response.status_code == 201, reservation_response.json()

    response = client.get(
        "/reservations/me",
        headers={
            "Authorization": f"Bearer {client_token}"
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

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_admin_lista_reservas@example.com",
        identificacion="700700700"
    )

    reservation_response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"]
    )

    assert reservation_response.status_code == 201, reservation_response.json()

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
    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_no_admin_reservas@example.com",
        identificacion="800800800"
    )

    response = client.get(
        "/reservations/",
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    assert response.status_code == 403


def test_client_can_get_own_reservation_by_id(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_get_own_reserva@example.com",
        identificacion="900900900"
    )

    reservation_response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"]
    )

    assert reservation_response.status_code == 201, reservation_response.json()

    reservation = reservation_response.json()

    response = client.get(
        f"/reservations/{reservation['id_reserva']}",
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["id_reserva"] == reservation["id_reserva"]


def test_client_cannot_get_other_client_reservation(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    owner_token, owner_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_dueno_reserva@example.com",
        identificacion="910910910"
    )

    other_token, other_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_otro_reserva@example.com",
        identificacion="920920920"
    )

    reservation_response = create_reservation(
        client,
        owner_token,
        package_id=package["id_paquete_turistico"]
    )

    assert reservation_response.status_code == 201, reservation_response.json()

    reservation = reservation_response.json()

    response = client.get(
        f"/reservations/{reservation['id_reserva']}",
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

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_admin_actualiza_reserva@example.com",
        identificacion="930930930"
    )

    reservation_response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"]
    )

    assert reservation_response.status_code == 201, reservation_response.json()

    reservation = reservation_response.json()

    response = client.patch(
        f"/reservations/{reservation['id_reserva']}/status",
        json={
            "estado": RESERVATION_STATUS_CONFIRMED
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["estado"] == RESERVATION_STATUS_CONFIRMED


def test_create_reservation_creates_email_notification(client, db_session):
    package, admin_token = create_package_ready_for_reservation(
        client,
        db_session
    )

    client_token, client_profile = create_client_with_token(
        client,
        db_session,
        email="cliente_notificacion_reserva@example.com",
        identificacion="940940940"
    )

    response = create_reservation(
        client,
        client_token,
        package_id=package["id_paquete_turistico"],
        cantidad_personas=1,
        acompanantes=[]
    )

    assert response.status_code == 201, response.json()

    reservation = response.json()

    db_session.rollback()
    db_session.expire_all()

    notification = (
        db_session.query(NotificationEmailModel)
        .filter(
            NotificationEmailModel.reservas_id_reserva
            == reservation["id_reserva"]
        )
        .filter(
            NotificationEmailModel.tipo_notificacion
            == NOTIFICATION_TYPE_RESERVATION_CONFIRMATION
        )
        .first()
    )

    assert notification is not None
    assert notification.estado_envio == "enviado_simulado"
    assert notification.reservas_id_reserva == reservation["id_reserva"]
    assert notification.usuarios_id_usuario is not None
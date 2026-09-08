from app.models.user_model import UserModel
from app.models.reservation_model import ReservationModel
from app.models.notification_email_model import NotificationEmailModel

from app.core.constants import (
    ADMIN_ROLE_ID,
    EMAIL_VERIFICATION_VERIFIED,
    PROVIDER_STATUS_APPROVED,
    RESERVATION_STATUS_CONFIRMED,
    NOTIFICATION_TYPE_PAYMENT_CONFIRMATION,
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
        nombre="Admin Pagos",
        email="admin_pagos@example.com"
    )

    make_user_admin(db_session, admin)

    admin_token = login_user(client, "admin_pagos@example.com")

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
    nombre: str = "Producto Para Pago"
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
    nombre: str = "Paquete Para Pago"
):
    response = client.post(
        "/packages/",
        json={
            "nombre": nombre,
            "descripcion": "Paquete turístico de prueba para pagos.",
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


def create_package_ready_for_payment(client, db_session):
    admin, admin_token = create_admin_with_token(client, db_session)

    create_verified_user(
        client,
        db_session,
        nombre="Proveedor Pago",
        email="proveedor_pago@example.com"
    )

    provider_token = login_user(client, "proveedor_pago@example.com")

    provider = create_provider_profile(
        client,
        provider_token,
        rut="930111222",
        nombre_empresa="Proveedor Pago"
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
        nombre="Producto Pago"
    )

    package = create_package(
        client,
        admin_token,
        producto_id=product["id_producto"],
        nombre="Paquete Pago"
    )

    return package, admin_token


def create_client_with_reservation(
    client,
    db_session,
    package_id: int,
    email: str,
    identificacion: str
):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Pago",
        email=email
    )

    client_token = login_user(client, email)

    create_client_profile(
        client,
        client_token,
        identificacion=identificacion
    )

    reservation_response = client.post(
        "/reservations/",
        json={
            "id_paquete_turistico": package_id,
            "fecha_reserva": "2026-09-10",
            "cantidad_personas": 2,
            "acompanantes": [
                {
                    "nombre": "Acompañante Pago",
                    "documento": "123123123",
                    "fecha_nacimiento": "1995-04-15"
                }
            ]
        },
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    assert reservation_response.status_code == 201, reservation_response.json()

    return client_token, reservation_response.json()


def create_payment(
    client,
    token: str,
    reserva_id: int,
    valor: str = "1300000.00",
    metodo_pago: str = "tarjeta"
):
    return client.post(
        "/payments/",
        json={
            "reserva_id": reserva_id,
            "metodo_pago": metodo_pago,
            "valor": valor
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )


def test_client_can_pay_own_pending_reservation(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_pago_propio@example.com",
        identificacion="100100100"
    )

    response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert response.status_code == 201, response.json()

    data = response.json()

    assert data["reserva_id"] == reservation["id_reserva"]
    assert data["estado_pago"] == "aprobado"
    assert data["valor"] == reservation["total_reserva"]
    assert "referencia_pago" in data


def test_payment_confirms_reservation(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_pago_confirma@example.com",
        identificacion="200200200"
    )

    payment_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert payment_response.status_code == 201, payment_response.json()

    db_session.rollback()
    db_session.expire_all()

    updated_reservation = (
        db_session.query(ReservationModel)
        .filter(ReservationModel.id_reserva == reservation["id_reserva"])
        .first()
    )

    assert updated_reservation.estado == RESERVATION_STATUS_CONFIRMED


def test_client_cannot_pay_other_client_reservation(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    owner_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_dueno_pago@example.com",
        identificacion="300300300"
    )

    other_token, other_reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_otro_pago@example.com",
        identificacion="400400400"
    )

    response = create_payment(
        client,
        other_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert response.status_code == 403


def test_cannot_pay_nonexistent_reservation(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente Pago Reserva Inexistente",
        email="cliente_pago_reserva_inexistente@example.com"
    )

    token = login_user(client, "cliente_pago_reserva_inexistente@example.com")

    create_client_profile(
        client,
        token,
        identificacion="500500500"
    )

    response = create_payment(
        client,
        token,
        reserva_id=999,
        valor="100000.00"
    )

    assert response.status_code == 404


def test_cannot_pay_with_wrong_value(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_pago_valor_incorrecto@example.com",
        identificacion="600600600"
    )

    response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor="1000.00"
    )

    assert response.status_code == 400


def test_cannot_pay_same_reservation_twice(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_pago_doble@example.com",
        identificacion="700700700"
    )

    first_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert first_response.status_code == 201, first_response.json()

    second_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert second_response.status_code == 400


def test_client_can_list_own_payments(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_lista_pagos@example.com",
        identificacion="800800800"
    )

    payment_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert payment_response.status_code == 201, payment_response.json()

    response = client.get(
        "/payments/me",
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    assert response.json()[0]["reserva_id"] == reservation["id_reserva"]


def test_admin_can_list_all_payments(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_admin_lista_pagos@example.com",
        identificacion="900900900"
    )

    payment_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert payment_response.status_code == 201, payment_response.json()

    response = client.get(
        "/payments/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_normal_client_cannot_list_all_payments(client, db_session):
    create_verified_user(
        client,
        db_session,
        nombre="Cliente No Admin Pagos",
        email="cliente_no_admin_pagos@example.com"
    )

    token = login_user(client, "cliente_no_admin_pagos@example.com")

    create_client_profile(
        client,
        token,
        identificacion="910910910"
    )

    response = client.get(
        "/payments/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_admin_can_get_payment_by_id(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_pago_por_id@example.com",
        identificacion="920920920"
    )

    payment_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert payment_response.status_code == 201, payment_response.json()

    id_pago = payment_response.json()["id_pago"]

    response = client.get(
        f"/payments/{id_pago}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["id_pago"] == id_pago


def test_normal_client_cannot_get_payment_by_id(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_no_admin_pago_id@example.com",
        identificacion="930930930"
    )

    payment_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert payment_response.status_code == 201, payment_response.json()

    id_pago = payment_response.json()["id_pago"]

    response = client.get(
        f"/payments/{id_pago}",
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )

    assert response.status_code == 403


def test_payment_creates_email_notification(client, db_session):
    package, admin_token = create_package_ready_for_payment(client, db_session)

    client_token, reservation = create_client_with_reservation(
        client,
        db_session,
        package_id=package["id_paquete_turistico"],
        email="cliente_notificacion_pago@example.com",
        identificacion="940940940"
    )

    payment_response = create_payment(
        client,
        client_token,
        reserva_id=reservation["id_reserva"],
        valor=reservation["total_reserva"]
    )

    assert payment_response.status_code == 201, payment_response.json()

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
            == NOTIFICATION_TYPE_PAYMENT_CONFIRMATION
        )
        .first()
    )

    assert notification is not None
    assert notification.estado_envio == "enviado_simulado"
    assert notification.reservas_id_reserva == reservation["id_reserva"]
    assert notification.usuarios_id_usuario is not None
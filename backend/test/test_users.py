def test_create_user_success(client):
    response = client.post(
        "/users/",
        json={
            "nombre": "Mario Test",
            "email": "mario_test@example.com",
            "password": "123456"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["nombre"] == "Mario Test"
    assert data["email"] == "mario_test@example.com"
    assert data["rol_id"] == 2
    assert data["verificacion_email"] == "pendiente"
    assert "contrasena_hash" not in data
    assert "password" not in data


def test_create_user_duplicate_email(client):
    client.post(
        "/users/",
        json={
            "nombre": "Usuario Uno",
            "email": "duplicado@example.com",
            "password": "123456"
        }
    )

    response = client.post(
        "/users/",
        json={
            "nombre": "Usuario Dos",
            "email": "duplicado@example.com",
            "password": "123456"
        }
    )

    assert response.status_code == 400

def test_create_user_invalid_email(client):
    response = client.post(
        "/users/",
        json={
            "nombre": "Mario Test",
            "email": "correo-invalido",
            "password": "123456"
        }
    )

    assert response.status_code == 422


def test_create_user_short_password(client):
    response = client.post(
        "/users/",
        json={
            "nombre": "Mario Test",
            "email": "short_password@example.com",
            "password": "123"
        }
    )

    assert response.status_code == 422
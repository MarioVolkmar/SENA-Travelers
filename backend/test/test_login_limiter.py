from app.core import login_limiter
from app.core.constants import EMAIL_VERIFICATION_VERIFIED
from app.models.user_model import UserModel


def create_verified_user(client, db_session, email="limite@example.com", password="123456"):
    client.post("/users/", json={"nombre": "Usuario Límite", "email": email, "password": password})
    user = db_session.query(UserModel).filter(UserModel.email == email).first()
    user.verificacion_email = EMAIL_VERIFICATION_VERIFIED
    db_session.commit()


def login(client, email, password):
    return client.post("/users/login", json={"email": email, "password": password})


def test_email_is_blocked_after_max_failed_attempts(client, db_session):
    create_verified_user(client, db_session)

    for _ in range(login_limiter.MAX_ATTEMPTS):
        assert login(client, "limite@example.com", "malaclave").status_code == 401

    blocked = login(client, "limite@example.com", "malaclave")
    assert blocked.status_code == 429
    assert "Demasiados intentos" in blocked.json()["detail"]
    assert int(blocked.headers["Retry-After"]) > 0


def test_blocked_email_cannot_login_even_with_right_password(client, db_session):
    create_verified_user(client, db_session)

    for _ in range(login_limiter.MAX_ATTEMPTS):
        login(client, "limite@example.com", "malaclave")

    assert login(client, "limite@example.com", "123456").status_code == 429


def test_successful_login_resets_failed_attempts(client, db_session):
    create_verified_user(client, db_session)

    for _ in range(login_limiter.MAX_ATTEMPTS - 1):
        login(client, "limite@example.com", "malaclave")

    assert login(client, "limite@example.com", "123456").status_code == 200

    # Después del ingreso correcto el contador vuelve a cero
    for _ in range(login_limiter.MAX_ATTEMPTS - 1):
        assert login(client, "limite@example.com", "malaclave").status_code == 401


def test_block_is_per_email(client, db_session):
    create_verified_user(client, db_session, email="bloqueado@example.com")
    create_verified_user(client, db_session, email="libre@example.com")

    for _ in range(login_limiter.MAX_ATTEMPTS):
        login(client, "bloqueado@example.com", "malaclave")

    assert login(client, "bloqueado@example.com", "123456").status_code == 429
    assert login(client, "libre@example.com", "123456").status_code == 200


def test_ip_is_blocked_after_many_failures_with_different_emails(client):
    for index in range(login_limiter.MAX_ATTEMPTS_PER_IP):
        login(client, f"no_existe_{index}@example.com", "malaclave")

    assert login(client, "otro_correo@example.com", "malaclave").status_code == 429

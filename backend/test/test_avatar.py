import pytest

from app.core import storage
from app.services import google_auth_service

from test_reservations import create_user, login_user, verify_user_email

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
CDN = "https://cdn.travelers.test"


class FakeS3:
    """S3 en memoria: los tests nunca tocan el bucket real."""

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType, CacheControl):
        self.objects[Key] = {"bucket": Bucket, "body": Body, "content_type": ContentType}

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)


@pytest.fixture(autouse=True)
def fake_s3(monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(storage, "s3_client", lambda: s3)
    monkeypatch.setenv("S3_BUCKET", "travelers-test")
    monkeypatch.setenv("CLOUDFRONT_URL", CDN)
    return s3


def user_token(client, db_session, email="foto@example.com"):
    create_user(client, "Usuario Foto", email)
    verify_user_email(db_session, email)
    return login_user(client, email)


def upload(client, token, data, filename="foto.png", content_type="image/png"):
    return client.post(
        "/users/me/avatar",
        files={"file": (filename, data, content_type)},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_avatar_is_uploaded_to_s3_and_served_by_cloudfront(client, db_session, fake_s3):
    token = user_token(client, db_session)

    response = upload(client, token, PNG)

    assert response.status_code == 200, response.json()
    foto_url = response.json()["foto_url"]
    assert foto_url.startswith(f"{CDN}/avatars/") and foto_url.endswith(".png")

    key = foto_url[len(CDN) + 1:]
    assert fake_s3.objects[key]["body"] == PNG
    assert fake_s3.objects[key]["bucket"] == "travelers-test"
    assert fake_s3.objects[key]["content_type"] == "image/png"


def test_replacing_avatar_deletes_previous_object(client, db_session, fake_s3):
    token = user_token(client, db_session)

    upload(client, token, PNG)
    second = upload(client, token, JPG, "foto.jpg", "image/jpeg").json()["foto_url"]

    assert list(fake_s3.objects) == [second[len(CDN) + 1:]]


def test_rejects_files_that_are_not_images(client, db_session, fake_s3):
    token = user_token(client, db_session)

    # El navegador dice que es una imagen, pero el contenido es texto
    response = upload(client, token, b"<html>no soy una imagen</html>", "foto.png", "image/png")

    assert response.status_code == 400
    assert fake_s3.objects == {}


def test_rejects_images_over_2mb(client, db_session):
    token = user_token(client, db_session)

    response = upload(client, token, PNG + b"\x00" * (2 * 1024 * 1024))

    assert response.status_code == 400
    assert "2 MB" in response.json()["detail"]


def test_user_can_delete_avatar(client, db_session, fake_s3):
    token = user_token(client, db_session)
    upload(client, token, PNG)

    response = client.delete("/users/me/avatar", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["foto_url"] is None
    assert fake_s3.objects == {}


def test_upload_without_bucket_returns_503(client, db_session, monkeypatch):
    token = user_token(client, db_session)
    monkeypatch.delenv("S3_BUCKET")

    response = upload(client, token, PNG)

    assert response.status_code == 503


def test_avatar_requires_login(client):
    response = client.post("/users/me/avatar", files={"file": ("f.png", PNG, "image/png")})

    assert response.status_code == 401


def fake_google(monkeypatch, picture):
    payload = {
        "iss": "https://accounts.google.com",
        "email": "confoto@gmail.com",
        "email_verified": True,
        "name": "Con Foto",
        "sub": "998877",
        "picture": picture,
    }
    monkeypatch.setattr(google_auth_service, "verify_google_credential", lambda credential: payload)


def test_google_account_uses_google_picture(client, monkeypatch):
    fake_google(monkeypatch, "https://lh3.googleusercontent.com/a/foto")

    token = client.post("/users/google", json={"credential": "x" * 30}).json()["access_token"]
    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"}).json()

    assert me["foto_url"] == "https://lh3.googleusercontent.com/a/foto"


def test_uploaded_avatar_is_not_replaced_by_google_picture(client, db_session, monkeypatch):
    token = user_token(client, db_session, email="confoto@gmail.com")
    uploaded = upload(client, token, PNG).json()["foto_url"]
    fake_google(monkeypatch, "https://lh3.googleusercontent.com/a/foto")

    google_token = client.post("/users/google", json={"credential": "x" * 30}).json()["access_token"]
    me = client.get("/users/me", headers={"Authorization": f"Bearer {google_token}"}).json()

    assert me["foto_url"] == uploaded


def test_deleting_google_picture_does_not_touch_s3(client, monkeypatch, fake_s3):
    fake_google(monkeypatch, "https://lh3.googleusercontent.com/a/foto")
    token = client.post("/users/google", json={"credential": "x" * 30}).json()["access_token"]

    response = client.delete("/users/me/avatar", headers={"Authorization": f"Bearer {token}"})

    assert response.json()["foto_url"] is None
    assert fake_s3.objects == {}

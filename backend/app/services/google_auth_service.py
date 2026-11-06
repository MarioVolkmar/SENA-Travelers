import os

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


def get_google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def verify_google_credential(credential: str) -> dict:
    """
    Verifica el ID token que entrega el botón de Google en el frontend y
    devuelve sus datos (email, name, email_verified, sub...).

    Comprueba la firma con las llaves públicas de Google, la expiración,
    el emisor y que el token se haya emitido para NUESTRO client id.
    """
    client_id = get_google_client_id()

    if not client_id:
        raise RuntimeError("El inicio de sesión con Google no está configurado (falta GOOGLE_CLIENT_ID)")

    try:
        payload = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id
        )
    except ValueError as error:
        raise PermissionError("El token de Google no es válido o expiró") from error

    if payload.get("iss") not in GOOGLE_ISSUERS:
        raise PermissionError("El token de Google no es válido")

    if not payload.get("email") or not payload.get("email_verified"):
        raise PermissionError("Tu cuenta de Google no tiene un correo verificado")

    return payload

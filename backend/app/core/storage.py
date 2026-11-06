"""
Almacenamiento de archivos en Amazon S3 (servidos por CloudFront).

Las fotos de perfil se guardan en el mismo bucket que las imágenes de los
paquetes, dentro de la carpeta "avatars/". En la base de datos solo se guarda
la clave (p. ej. "avatars/21_ab12.jpg"); la URL pública se arma con CLOUDFRONT_URL.

Credenciales: boto3 las busca solo, en este orden habitual:
  1. Variables AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (en .env para desarrollo)
  2. ~/.aws/credentials
  3. El rol IAM de la instancia (recomendado en EC2: no hay llaves en el servidor)
"""
import os
from functools import lru_cache
from urllib.parse import quote

import boto3
from dotenv import load_dotenv

load_dotenv()

AVATAR_PREFIX = "avatars/"
AVATAR_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
PACKAGE_IMAGE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

IMAGE_CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def detect_image_extension(data: bytes):
    """
    Revisa las primeras bytes del archivo ("magic bytes") para saber si es
    una imagen real. No se confía en el nombre ni en el Content-Type del navegador.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"

    return None


class StorageNotConfigured(RuntimeError):
    pass


def bucket_name() -> str:
    bucket = os.getenv("S3_BUCKET", "").strip()

    if not bucket:
        raise StorageNotConfigured("El almacenamiento de imágenes no está configurado (falta S3_BUCKET)")

    return bucket


@lru_cache(maxsize=1)
def _s3_client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))


def s3_client():
    """Cliente de S3 (función aparte para poder reemplazarlo en los tests)."""
    return _s3_client()


def upload_file(key: str, data: bytes, content_type: str):
    s3_client().put_object(
        Bucket=bucket_name(),
        Key=key,
        Body=data,
        ContentType=content_type,
        # El nombre de cada archivo es único, así que puede guardarse en caché un año
        CacheControl="public, max-age=31536000, immutable",
    )


def delete_file(key: str):
    s3_client().delete_object(Bucket=bucket_name(), Key=key)


def public_url(key: str):
    """URL de CloudFront para una clave de S3 (None si CLOUDFRONT_URL no está configurada)."""
    cloudfront_url = os.getenv("CLOUDFRONT_URL", "").strip().rstrip("/")

    if not cloudfront_url:
        return None

    if not cloudfront_url.startswith(("http://", "https://")):
        cloudfront_url = f"https://{cloudfront_url}"

    return f"{cloudfront_url}/{quote(key, safe='/')}"


def is_avatar_key(value) -> bool:
    return bool(value) and value.startswith(AVATAR_PREFIX) and ".." not in value


def photo_public_url(foto_url):
    """
    Convierte lo guardado en usuarios.foto_url en una URL que el navegador pueda usar:
    - "avatars/..."  → foto subida a S3, se sirve por CloudFront
    - "https://..."  → foto externa (cuenta de Google)
    """
    if not foto_url:
        return None

    if foto_url.startswith("https://"):
        return foto_url

    if is_avatar_key(foto_url):
        return public_url(foto_url)

    return None

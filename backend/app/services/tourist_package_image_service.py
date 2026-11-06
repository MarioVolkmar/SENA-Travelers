import re
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core import storage

# Claves que genera la consola al subir: "<id_paquete>/<uuid de 32 caracteres>.<ext>"
UPLOADED_KEY_PATTERN = re.compile(r"^\d+/[0-9a-f]{32}\.(jpg|png|webp)$")
from app.core.constants import ADMIN_ROLE_ID
from app.models.tourist_package_image_model import TouristPackageImageModel
from app.models.user_model import UserModel
from app.repositories.tourist_package_image_repository import (
    TouristPackageImageRepository
)
from app.repositories.tourist_package_repository import (
    TouristPackageRepository
)
from app.schemas.tourist_package_image_schema import TouristPackageImageCreate


class TouristPackageImageService:
    """
    Gestiona las imágenes de los paquetes turísticos.

    Las imágenes se almacenan en S3 y se sirven a través de CloudFront.
    En la base de datos solo se guarda la clave (s3_key) de cada imagen,
    que debe estar dentro de la carpeta del paquete: "<id_paquete>/archivo.jpg".
    """

    def __init__(self, db: Session):
        self.image_repository = TouristPackageImageRepository(db)
        self.package_repository = TouristPackageRepository(db)

    # ---------------------------------------------------------------
    # Validaciones internas
    # ---------------------------------------------------------------

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError(
                "Solo los administradores pueden gestionar imágenes"
            )

    def _get_package_or_raise(self, paquete_id: int):
        package = self.package_repository.find_by_id(paquete_id)

        if package is None:
            raise LookupError("El paquete turístico no existe")

        return package

    def _get_image_of_package_or_raise(self, paquete_id: int, id_imagen: int):
        image = self.image_repository.find_by_id(id_imagen)

        if image is None or image.paquete_id != paquete_id:
            raise LookupError("La imagen no existe en este paquete")

        return image

    def _validate_s3_key(self, paquete_id: int, s3_key: str) -> str:
        s3_key = s3_key.strip()

        expected_prefix = f"{paquete_id}/"

        if not s3_key.startswith(expected_prefix):
            raise ValueError("La imagen no pertenece a la carpeta del paquete")

        relative_path = s3_key[len(expected_prefix):]
        segments = relative_path.split("/")

        invalid_segment = any(
            segment in ("", ".", "..")
            or "\\" in segment
            or any(ord(char) < 32 for char in segment)
            for segment in segments
        )

        if (
            not relative_path
            or invalid_segment
            or "?" in relative_path
            or "#" in relative_path
        ):
            raise ValueError("La clave S3 contiene una ruta inválida")

        return s3_key

    # ---------------------------------------------------------------
    # URL pública
    # ---------------------------------------------------------------

    @staticmethod
    def generate_image_url(s3_key: str) -> Optional[str]:
        """
        Construye la URL pública de la imagen. Si CLOUDFRONT_URL no está
        configurada devuelve None en lugar de romper la petición.
        """
        return storage.public_url(s3_key)

    # ---------------------------------------------------------------
    # Casos de uso
    # ---------------------------------------------------------------

    def create_image(
        self,
        paquete_id: int,
        image_data: TouristPackageImageCreate,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)
        self._get_package_or_raise(paquete_id)

        s3_key = self._validate_s3_key(paquete_id, image_data.s3_key)

        if self.image_repository.find_by_s3_key(paquete_id, s3_key):
            raise ValueError("La imagen ya está registrada en este paquete")

        if image_data.es_portada and self.image_repository.find_cover_by_package_id(paquete_id):
            raise ValueError("El paquete ya tiene una imagen de portada")

        image = TouristPackageImageModel(
            paquete_id=paquete_id,
            s3_key=s3_key,
            es_portada=image_data.es_portada,
            orden=image_data.orden
        )

        return self.image_repository.create_image(image)

    def upload_image(
        self,
        paquete_id: int,
        data: bytes,
        es_portada: bool,
        orden: int,
        current_user: UserModel
    ):
        """Sube la imagen a S3 en la carpeta del paquete ("<id>/<uuid>.jpg") y la registra."""
        self._ensure_admin(current_user)
        self._get_package_or_raise(paquete_id)

        if not data:
            raise ValueError("El archivo está vacío")

        if len(data) > storage.PACKAGE_IMAGE_MAX_BYTES:
            raise ValueError("La imagen no puede superar los 5 MB")

        extension = storage.detect_image_extension(data)

        if extension is None:
            raise ValueError("Formato no permitido. Usa una imagen JPG, PNG o WEBP")

        if es_portada and self.image_repository.find_cover_by_package_id(paquete_id):
            raise ValueError("El paquete ya tiene una imagen de portada")

        key = f"{paquete_id}/{uuid4().hex}.{extension}"
        storage.upload_file(key, data, storage.IMAGE_CONTENT_TYPES[extension])

        image = TouristPackageImageModel(
            paquete_id=paquete_id,
            s3_key=key,
            es_portada=es_portada,
            orden=orden
        )

        try:
            return self.image_repository.create_image(image)
        except Exception:
            storage.delete_file(key)
            raise

    def list_images_by_package(self, paquete_id: int):
        self._get_package_or_raise(paquete_id)

        return self.image_repository.list_by_package_id(paquete_id)

    def get_cover_by_package(self, paquete_id: int):
        self._get_package_or_raise(paquete_id)

        return self.image_repository.find_cover_by_package_id(paquete_id)

    def list_all_covers(self):
        return self.image_repository.list_covers()

    def set_cover(
        self,
        paquete_id: int,
        id_imagen: int,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)
        self._get_package_or_raise(paquete_id)

        image = self._get_image_of_package_or_raise(paquete_id, id_imagen)

        return self.image_repository.set_cover(image)

    def delete_image(
        self,
        paquete_id: int,
        id_imagen: int,
        current_user: UserModel
    ):
        self._ensure_admin(current_user)
        self._get_package_or_raise(paquete_id)

        image = self._get_image_of_package_or_raise(paquete_id, id_imagen)
        s3_key = image.s3_key

        self.image_repository.delete_image(image)

        # Solo se borra de S3 si la subió la consola; las cargadas a mano solo se desvinculan
        if UPLOADED_KEY_PATTERN.match(s3_key):
            try:
                storage.delete_file(s3_key)
            except Exception:
                pass

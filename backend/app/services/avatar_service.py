from uuid import uuid4

from sqlalchemy.orm import Session

from app.core import storage
from app.core.storage import IMAGE_CONTENT_TYPES, detect_image_extension
from app.models.user_model import UserModel
from app.repositories.user_repository import UserRepository


class AvatarService:
    """Fotos de perfil guardadas en S3, dentro de la carpeta avatars/ del bucket."""

    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def _delete_previous(self, previous):
        # Solo se borran fotos propias de S3, nunca la URL de Google
        if storage.is_avatar_key(previous):
            try:
                storage.delete_file(previous)
            except Exception:
                # Si falla el borrado queda un archivo huérfano, pero el usuario no pierde su foto nueva
                pass

    def upload_avatar(self, current_user: UserModel, data: bytes):
        if not data:
            raise ValueError("El archivo está vacío")

        if len(data) > storage.AVATAR_MAX_BYTES:
            raise ValueError("La imagen no puede superar los 2 MB")

        extension = detect_image_extension(data)

        if extension is None:
            raise ValueError("Formato no permitido. Usa una imagen JPG, PNG o WEBP")

        key = f"{storage.AVATAR_PREFIX}{current_user.id_usuario}_{uuid4().hex}.{extension}"
        storage.upload_file(key, data, IMAGE_CONTENT_TYPES[extension])

        previous = current_user.foto_url

        try:
            user = self.user_repository.update_photo(current_user, key)
        except Exception:
            # Si no se pudo guardar en la base, no deja el archivo suelto en S3
            storage.delete_file(key)
            raise

        self._delete_previous(previous)

        return user

    def delete_avatar(self, current_user: UserModel):
        previous = current_user.foto_url

        user = self.user_repository.update_photo(current_user, None)
        self._delete_previous(previous)

        return user

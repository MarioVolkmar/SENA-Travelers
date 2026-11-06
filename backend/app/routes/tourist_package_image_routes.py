from typing import List, Optional

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core import storage
from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.schemas.tourist_package_image_schema import (
    TouristPackageImageCreate,
    TouristPackageImageResponse
)
from app.services.tourist_package_image_service import (
    TouristPackageImageService
)


router = APIRouter(
    prefix="/packages",
    tags=["Package Images"]
)


def build_image_response(image) -> TouristPackageImageResponse:
    return TouristPackageImageResponse(
        id_imagen=image.id_imagen,
        paquete_id=image.paquete_id,
        s3_key=image.s3_key,
        es_portada=image.es_portada,
        orden=image.orden,
        imagen_url=TouristPackageImageService.generate_image_url(image.s3_key)
    )


def handle_service_errors(error: Exception):
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))

    if isinstance(error, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))

    if isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    raise error


@router.get(
    "/images/covers",
    response_model=List[TouristPackageImageResponse]
)
def list_all_covers(db: Session = Depends(get_db)):
    """Portadas de todos los paquetes (útil para el listado del frontend)."""
    service = TouristPackageImageService(db)

    return [build_image_response(image) for image in service.list_all_covers()]


@router.post(
    "/{paquete_id}/images",
    response_model=TouristPackageImageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_package_image(
    paquete_id: int,
    image_data: TouristPackageImageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        service = TouristPackageImageService(db)
        image = service.create_image(paquete_id, image_data, current_user)

        return build_image_response(image)

    except (PermissionError, LookupError, ValueError) as error:
        handle_service_errors(error)


@router.post(
    "/{paquete_id}/images/upload",
    response_model=TouristPackageImageResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_package_image(
    paquete_id: int,
    file: UploadFile = File(...),
    es_portada: bool = Form(False),
    orden: int = Form(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Sube una imagen a S3 (carpeta del paquete) y la registra. Solo administradores."""
    data = await file.read(storage.PACKAGE_IMAGE_MAX_BYTES + 1)

    try:
        service = TouristPackageImageService(db)
        image = service.upload_image(paquete_id, data, es_portada, orden, current_user)

        return build_image_response(image)

    except (PermissionError, LookupError, ValueError) as error:
        handle_service_errors(error)

    except storage.StorageNotConfigured as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))

    except (BotoCoreError, ClientError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No fue posible guardar la imagen en S3. Intenta de nuevo."
        )


@router.get(
    "/{paquete_id}/images",
    response_model=List[TouristPackageImageResponse]
)
def list_package_images(
    paquete_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = TouristPackageImageService(db)

        return [
            build_image_response(image)
            for image in service.list_images_by_package(paquete_id)
        ]

    except LookupError as error:
        handle_service_errors(error)


@router.get(
    "/{paquete_id}/images/cover",
    response_model=Optional[TouristPackageImageResponse]
)
def get_package_cover(
    paquete_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = TouristPackageImageService(db)
        image = service.get_cover_by_package(paquete_id)

        return build_image_response(image) if image else None

    except LookupError as error:
        handle_service_errors(error)


@router.patch(
    "/{paquete_id}/images/{id_imagen}/cover",
    response_model=TouristPackageImageResponse
)
def set_package_cover(
    paquete_id: int,
    id_imagen: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        service = TouristPackageImageService(db)
        image = service.set_cover(paquete_id, id_imagen, current_user)

        return build_image_response(image)

    except (PermissionError, LookupError) as error:
        handle_service_errors(error)


@router.delete(
    "/{paquete_id}/images/{id_imagen}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_package_image(
    paquete_id: int,
    id_imagen: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        service = TouristPackageImageService(db)
        service.delete_image(paquete_id, id_imagen, current_user)

    except (PermissionError, LookupError) as error:
        handle_service_errors(error)

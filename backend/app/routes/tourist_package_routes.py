from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.models.user_model import UserModel

from app.schemas.tourist_package_schema import (
    TouristPackageCreate,
    TouristPackageUpdate,
    TouristPackageStatusUpdate,
    TouristPackageResponse,
)

from app.services.tourist_package_service import TouristPackageService


router = APIRouter(
    prefix="/packages",
    tags=["Tourist Packages"]
)


@router.post(
    "/",
    response_model=TouristPackageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_package(
    package_data: TouristPackageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.create_package(
            package_data,
            current_user
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=List[TouristPackageResponse]
)
def list_active_packages(
    db: Session = Depends(get_db)
):
    tourist_package_service = TouristPackageService(db)

    return tourist_package_service.list_active_packages()


@router.get(
    "/admin",
    response_model=List[TouristPackageResponse]
)
def list_packages_admin(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.list_packages(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/admin/{id_paquete_turistico}",
    response_model=TouristPackageResponse
)
def get_package_by_id_admin(
    id_paquete_turistico: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.get_package_by_id_admin(
            id_paquete_turistico,
            current_user
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get(
    "/city/{ciudad_id}",
    response_model=List[TouristPackageResponse]
)
def list_active_packages_by_city(
    ciudad_id: int,
    db: Session = Depends(get_db)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.list_active_packages_by_city(ciudad_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/{id_paquete_turistico}",
    response_model=TouristPackageResponse
)
def get_package_by_id(
    id_paquete_turistico: int,
    db: Session = Depends(get_db)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.get_package_by_id(id_paquete_turistico)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.patch(
    "/{id_paquete_turistico}",
    response_model=TouristPackageResponse
)
def update_package(
    id_paquete_turistico: int,
    package_data: TouristPackageUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.update_package(
            id_paquete_turistico,
            package_data,
            current_user
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.patch(
    "/{id_paquete_turistico}/status",
    response_model=TouristPackageResponse
)
def update_package_status(
    id_paquete_turistico: int,
    status_data: TouristPackageStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        tourist_package_service = TouristPackageService(db)

        return tourist_package_service.update_package_status(
            id_paquete_turistico,
            status_data,
            current_user
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
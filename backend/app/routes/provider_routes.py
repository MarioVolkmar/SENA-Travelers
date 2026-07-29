from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.models.user_model import UserModel

from app.schemas.provider_schema import (
    ProviderCreate,
    ProviderUpdate,
    ProviderVerificationUpdate,
    ProviderResponse
)

from app.services.provider_service import ProviderService


router = APIRouter(
    prefix="/providers",
    tags=["Providers"]
)


@router.post(
    "/me",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_provider(
    provider_data: ProviderCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.create_provider(provider_data, current_user)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/me",
    response_model=ProviderResponse
)
def get_self_provider(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.get_self_provider(current_user)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=List[ProviderResponse]
)
def list_providers(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.list_providers(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/pending",
    response_model=List[ProviderResponse]
)
def list_pending_providers(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.list_pending_providers(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/{id_proveedor}",
    response_model=ProviderResponse
)
def get_provider_by_id(
    id_proveedor: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.get_provider_by_id(id_proveedor, current_user)

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


@router.patch(
    "/{id_proveedor}",
    response_model=ProviderResponse
)
def update_provider(
    id_proveedor: int,
    provider_data: ProviderUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.update_provider(
            id_proveedor,
            provider_data,
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
    "/{id_proveedor}/verification-status",
    response_model=ProviderResponse
)
def update_provider_verification_status(
    id_proveedor: int,
    verification_data: ProviderVerificationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        provider_service = ProviderService(db)
        return provider_service.update_verification_status(
            id_proveedor,
            verification_data,
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
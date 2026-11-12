from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.models.user_model import UserModel

from app.schemas.reservation_schema import (
    ReservationCreate,
    ReservationStatusUpdate,
    ReservationResponse,
    PackageAvailabilityResponse,
    CancellationPolicyResponse,
    CancellationPreviewResponse,
)

from app.services.reservation_service import ReservationService


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)


@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_reservation(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.create_reservation(
            reservation_data,
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
    "/me",
    response_model=List[ReservationResponse]
)
def list_my_reservations(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.list_my_reservations(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=List[ReservationResponse]
)
def list_reservations_admin(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.list_reservations(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/availability/{id_paquete_turistico}",
    response_model=PackageAvailabilityResponse
)
def get_package_availability(
    id_paquete_turistico: int,
    db: Session = Depends(get_db)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.get_package_availability(id_paquete_turistico)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get(
    "/cancellation-policy",
    response_model=CancellationPolicyResponse
)
def get_cancellation_policy(db: Session = Depends(get_db)):
    """Días de cancelación gratuita y porcentaje de penalidad (público)."""
    return ReservationService(db).get_cancellation_policy()


@router.get(
    "/{id_reserva}/cancellation",
    response_model=CancellationPreviewResponse
)
def preview_cancellation(
    id_reserva: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Muestra al cliente cuánto se le cobraría y reembolsaría si cancela hoy."""
    try:
        return ReservationService(db).preview_cancellation(id_reserva, current_user)

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
    "/{id_reserva}/cancel",
    response_model=ReservationResponse
)
def cancel_my_reservation(
    id_reserva: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.cancel_my_reservation(id_reserva, current_user)

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


@router.get("/{id_reserva}/detail")
def get_reservation_detail(
    id_reserva: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Ficha completa de la reserva para la consola (solo administrador)."""
    try:
        return ReservationService(db).admin_detail(id_reserva, current_user)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.get(
    "/{id_reserva}",
    response_model=ReservationResponse
)
def get_reservation_by_id(
    id_reserva: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.get_reservation_by_id(
            id_reserva,
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


@router.patch(
    "/{id_reserva}/status",
    response_model=ReservationResponse
)
def update_reservation_status(
    id_reserva: int,
    status_data: ReservationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        reservation_service = ReservationService(db)

        return reservation_service.update_reservation_status(
            id_reserva,
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
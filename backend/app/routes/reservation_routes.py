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
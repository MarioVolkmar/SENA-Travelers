from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        user_service = UserService(db)
        return user_service.create_user(user_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=List[UserResponse]
)
def list_users(db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.list_users()


@router.get(
    "/{id_usuario}",
    response_model=UserResponse
)
def get_user_by_id(
    id_usuario: int,
    db: Session = Depends(get_db)
):
    try:
        user_service = UserService(db)
        return user_service.get_user_by_id(id_usuario)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.patch(
    "/{id_usuario}/deactivate",
    response_model=UserResponse
)
def deactivate_user(
    id_usuario: int,
    db: Session = Depends(get_db)
):
    try:
        user_service = UserService(db)
        return user_service.deactivate_user(id_usuario)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
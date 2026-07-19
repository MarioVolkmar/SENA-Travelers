from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin, TokenResponse, UserEmailUpdate, UserNameUpdate, UserPasswordUpdate, UserRoleUpdate
from app.services.user_service import UserService
from app.models.user_model import UserModel
from app.core.security import get_current_user


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
def list_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.list_users(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )
    
@router.get(
    "/me",
    response_model= UserResponse
    )
def current_user_active(
    current_user: UserModel = Depends(get_current_user)
):
    return current_user

@router.get(
    "/{id_usuario}",
    response_model=UserResponse
)
def get_user_by_id(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.get_user_by_id(id_usuario, current_user)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        ) 

@router.patch(
    "/{id_usuario}/deactivate",
    response_model=UserResponse
)
def deactivate_user(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.deactivate_user(id_usuario, current_user)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        ) 
    
@router.patch(
    "/{id_usuario}/activate",
    response_model= UserResponse
)
def activate_user(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.activate_user(id_usuario, current_user)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@router.patch(
    "/{id_usuario}/role",
    response_model=UserResponse
)
def update_user_rol(
    id_usuario: int,
    user_data : UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.update_user_role(id_usuario, user_data.rol_id, current_user)
    
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )  
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        ) 
    
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )   

@router.patch(
    "/{id_usuario}/name",
    response_model=UserResponse
)
def update_name(
    id_usuario: int,
    user_data : UserNameUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.update_name(id_usuario, user_data.nombre, current_user)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )  
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )  

@router.patch(
    "/{id_usuario}/email",
    response_model=UserResponse
)
def update_email(
    id_usuario: int,
    user_data : UserEmailUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.update_email(id_usuario, user_data.email, current_user)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )  
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        ) 
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )  
    
@router.patch(
    "/{id_usuario}/password",
    response_model=UserResponse
)
def update_password(
    id_usuario: int,
    user_data : UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service = UserService(db)
        return user_service.update_password(id_usuario, user_data.actual_password, user_data.new_password, current_user)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )  
    
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )  


@router.post("/login", response_model= TokenResponse)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db) 
):
    try: 
        user_service = UserService(db)
        return user_service.login_user(
            login_data.email,
            login_data.password
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error)
        )
    
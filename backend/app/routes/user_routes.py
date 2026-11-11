from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core import login_limiter
from app.database.connection import get_db
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin, TokenResponse, UserEmailUpdate, UserNameUpdate, UserPasswordUpdate, UserRoleUpdate, ForgotPasswordRequest, ResetPasswordRequest, GoogleLoginRequest, GoogleConfigResponse, UserPasswordReset
from app.services.user_service import UserService
from app.services.google_auth_service import get_google_client_id
from app.services.avatar_service import AvatarService
from app.core.storage import AVATAR_MAX_BYTES, StorageNotConfigured
from botocore.exceptions import BotoCoreError, ClientError
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
        return  user_service.create_user(user_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@router.post("/forgot-password")
def forgot_password(
    password_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)

    return user_service.request_password_reset(
        password_data.email
    )


@router.post("/reset-password")
def reset_password(
    password_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        user_service = UserService(db)

        return user_service.reset_password(
            password_data.token,
            password_data.new_password
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

@router.get(
    "/verify-email",
    response_model=UserResponse
)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    try:
        user_service = UserService(db)
        return user_service.verify_email(token)

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

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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

@router.patch(
    "/{id_usuario}/reset-password",
    response_model=UserResponse
)
def reset_password_by_admin(
    id_usuario : int,
    user_data : UserPasswordReset,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        user_service= UserService(db)
        return user_service.reset_password_by_admin(id_usuario, user_data.new_password, current_user)
    
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

@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Sube o reemplaza la foto de perfil (JPG, PNG o WEBP, máximo 2 MB)."""
    # Se lee un byte de más para detectar archivos demasiado grandes sin cargarlos completos
    data = await file.read(AVATAR_MAX_BYTES + 1)

    try:
        return AvatarService(db).upload_avatar(current_user, data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except StorageNotConfigured as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )

    except (BotoCoreError, ClientError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No fue posible guardar la imagen en S3. Intenta de nuevo."
        )


@router.delete("/me/avatar", response_model=UserResponse)
def delete_avatar(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Quita la foto de perfil (y la borra de S3 si era una foto subida)."""
    return AvatarService(db).delete_avatar(current_user)


@router.get("/google/config", response_model=GoogleConfigResponse)
def google_config():
    """Le indica al frontend si el inicio con Google está activo y con qué client id."""
    client_id = get_google_client_id()

    return {"enabled": bool(client_id), "client_id": client_id or None}


@router.post("/google", response_model=TokenResponse)
def login_with_google(
    google_data: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    """Inicia sesión o registra al usuario con el ID token del botón de Google."""
    try:
        user_service = UserService(db)
        return user_service.login_with_google(google_data.credential)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )


@router.post("/login", response_model= TokenResponse)
def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else None

    # Si el correo o la IP acumularon demasiados fallos, ni se revisa la contraseña
    try:
        login_limiter.ensure_allowed(login_data.email, client_ip)
    except login_limiter.TooManyAttemptsError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(error),
            headers={"Retry-After": str(error.retry_after)},
        )

    try:
        user_service = UserService(db)
        token = user_service.login_user(
            login_data.email,
            login_data.password
        )
    except PermissionError as error:
        login_limiter.register_failure(login_data.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error)
        )

    login_limiter.register_success(login_data.email)
    return token
    
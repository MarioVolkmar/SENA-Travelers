from passlib.context import CryptContext

from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.user_repository import UserRepository

import os
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = os.getenv("BACK_ALGORITHM")
SECRET_KEY = os.getenv("BACK_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
)
VALIDATION_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("VALIDATION_TOKEN_EXPIRE_MINUTES", 120)
)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def hash_password(password: str):
        return password_context.hash(password)

def verify_password(password : str, hash_password : str):
    return password_context.verify(password, hash_password)

def create_access_token(data : dict):
    payload = data.copy()

    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["purpose"] = "access"

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def create_email_verification_token(data: dict):
    payload = data.copy()

    payload["exp"] = datetime.utcnow() + timedelta(minutes = VALIDATION_TOKEN_EXPIRE_MINUTES)
    payload["purpose"] = "email_verification"

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_email_verification_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")
        purpose = payload.get("purpose")

        if user_id is None:
            raise PermissionError("Token inválido")

        if purpose != "email_verification":
            raise PermissionError("Token tipo inválido")

        try:
            return int(user_id)
        except ValueError:
            raise PermissionError("Token inválido")
        
    except JWTError:
        raise PermissionError("Token inválido o expirado")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")
        purpose = payload.get("purpose")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        if purpose != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tipo inválido"
            )

        user_repository = UserRepository(db)
        user = user_repository.find_by_id(int(user_id))

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )

        if user.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
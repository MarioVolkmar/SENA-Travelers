from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.services.client_service import ClientService
from app.schemas.client_schema import ClientCreate, ClientResponse, ClientUpdate
from app.models.user_model import UserModel

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

@router.post(
    "/me",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED
)
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        client_service = ClientService(db)
        return  client_service.create_client(client_data, current_user)

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
    response_model=ClientResponse,
)
def get_self_client(
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        client_service = ClientService(db)
        return  client_service.get_self_client(current_user)

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

@router.get(
    "/",
    response_model=List[ClientResponse],
)
def list_clients(
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try: 
        client_service = ClientService(db)
        return  client_service.list_clients(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        ) 
    
@router.get(
    "/user/{id_usuario}",
    response_model=ClientResponse,
)
def get_client_by_user_id(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        client_service = ClientService(db)
        return  client_service.get_client_by_id_user(id_usuario, current_user)
    
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
    "/{id_cliente}",
    response_model=ClientResponse,
)
def get_client_by_id(
    id_cliente: int,
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        client_service = ClientService(db)
        return  client_service.get_client_by_id(id_cliente, current_user)
    
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
    "/{id_cliente}/city",
    response_model=ClientResponse,
)
def update_client_city(
    id_cliente: int,
    data_client: ClientUpdate,
    db: Session = Depends(get_db),
    current_user : UserModel = Depends(get_current_user)
):
    try:
        client_service = ClientService(db)
        return  client_service.update_client_city(id_cliente, data_client.ciudad_id, current_user)
    
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
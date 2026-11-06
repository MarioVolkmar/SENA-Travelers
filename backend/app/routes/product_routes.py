# app/routes/product_routes.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.models.user_model import UserModel

from app.schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductProviderUpdate,
    ProductResponse,
    ProductTypeResponse,
    ProductUnitResponse,
)

from app.core.constants import PRODUCT_TYPES, PRODUCT_UNITS
from app.services.product_service import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.create_product(product_data, current_user)

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
    response_model=List[ProductResponse]
)
def list_active_products(
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    return product_service.list_active_products()


@router.get(
    "/types",
    response_model=List[ProductTypeResponse]
)
def list_product_types():
    """Catálogo de tipos de producto (hospedaje, alimentación, transporte...)."""
    return [
        {"clave": key, "nombre": name, "ejemplos": examples}
        for key, (name, examples) in PRODUCT_TYPES.items()
    ]


@router.get(
    "/units",
    response_model=List[ProductUnitResponse]
)
def list_product_units():
    """Unidades de cobro: por persona, por noche, por día o por servicio."""
    return [{"clave": key, "nombre": name} for key, name in PRODUCT_UNITS.items()]


@router.get(
    "/admin",
    response_model=List[ProductResponse]
)
def list_products_admin(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.list_products(current_user)

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.get(
    "/admin/{id_producto}",
    response_model=ProductResponse
)
def get_product_by_id_admin(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.get_product_by_id_admin(
            id_producto,
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
    response_model=List[ProductResponse]
)
def list_products_by_city(
    ciudad_id: int,
    db: Session = Depends(get_db)
):
    try:
        product_service = ProductService(db)
        return product_service.list_products_by_city(ciudad_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/provider/{proveedor_id}",
    response_model=List[ProductResponse]
)
def list_products_by_provider(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.list_products_by_provider(
            proveedor_id,
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
    "/{id_producto}",
    response_model=ProductResponse
)
def get_product_by_id(
    id_producto: int,
    db: Session = Depends(get_db)
):
    try:
        product_service = ProductService(db)
        return product_service.get_product_by_id(id_producto)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.patch(
    "/{id_producto}",
    response_model=ProductResponse
)
def update_product(
    id_producto: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.update_product(
            id_producto,
            product_data,
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
    "/{id_producto}/status",
    response_model=ProductResponse
)
def update_product_status(
    id_producto: int,
    status_data: ProductStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.update_product_status(
            id_producto,
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


@router.patch(
    "/{id_producto}/provider",
    response_model=ProductResponse
)
def update_product_provider(
    id_producto: int,
    provider_data: ProductProviderUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        product_service = ProductService(db)
        return product_service.update_product_provider(
            id_producto,
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
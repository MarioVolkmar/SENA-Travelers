from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.schemas.provider_payment_order_schema import (
    GenerateOrdersResponse,
    ProviderPaymentOrderAnnul,
    ProviderPaymentOrderPay,
    ProviderPaymentOrderResponse,
    SettingsResponse,
    SettingsUpdate,
)
from app.services.provider_payment_order_service import ProviderPaymentOrderService
from app.services.setting_service import SettingService

router = APIRouter(tags=["Provider Payments"])


def handle_errors(error: Exception):
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    raise error


# ---------------------------------------------------------------
# Órdenes de pago a proveedores
# ---------------------------------------------------------------

@router.get("/provider-payments/", response_model=List[ProviderPaymentOrderResponse])
def list_orders(
    estado: Optional[str] = Query(None),
    proveedor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Todas las órdenes (administrador), con filtros opcionales."""
    try:
        service = ProviderPaymentOrderService(db)
        return [service.serialize(order) for order in service.list_orders(current_user, estado, proveedor_id)]
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


@router.get("/provider-payments/me", response_model=List[ProviderPaymentOrderResponse])
def list_my_orders(
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Órdenes del proveedor que inició sesión."""
    try:
        service = ProviderPaymentOrderService(db)
        return [service.serialize(order) for order in service.list_my_orders(current_user, estado)]
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


@router.post("/provider-payments/generate", response_model=GenerateOrdersResponse)
def generate_missing_orders(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Genera las órdenes que falten para reservas ya confirmadas (administrador)."""
    try:
        created = ProviderPaymentOrderService(db).generate_missing(current_user)
        return {"ordenes_creadas": len(created)}
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


@router.get("/provider-payments/{id_orden}", response_model=ProviderPaymentOrderResponse)
def get_order(
    id_orden: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        service = ProviderPaymentOrderService(db)
        return service.serialize(service.get_order(id_orden, current_user))
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


@router.patch("/provider-payments/{id_orden}/approve", response_model=ProviderPaymentOrderResponse)
def approve_order(
    id_orden: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        service = ProviderPaymentOrderService(db)
        return service.serialize(service.approve(id_orden, current_user))
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


@router.patch("/provider-payments/{id_orden}/pay", response_model=ProviderPaymentOrderResponse)
def pay_order(
    id_orden: int,
    data: ProviderPaymentOrderPay,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Marca la orden como pagada con la referencia de la transferencia (simulada)."""
    try:
        service = ProviderPaymentOrderService(db)
        return service.serialize(service.mark_paid(id_orden, data.referencia_pago, data.nota, current_user))
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


@router.patch("/provider-payments/{id_orden}/annul", response_model=ProviderPaymentOrderResponse)
def annul_order(
    id_orden: int,
    data: ProviderPaymentOrderAnnul,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        service = ProviderPaymentOrderService(db)
        return service.serialize(service.annul(id_orden, data.nota, current_user))
    except (PermissionError, LookupError, ValueError) as error:
        handle_errors(error)


# ---------------------------------------------------------------
# Configuración del sistema (administrador)
# ---------------------------------------------------------------

@router.get("/settings/", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return SettingService(db).get_settings(current_user)
    except PermissionError as error:
        handle_errors(error)


@router.patch("/settings/", response_model=SettingsResponse)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return SettingService(db).update_settings(data.model_dump(exclude_unset=True), current_user)
    except PermissionError as error:
        handle_errors(error)

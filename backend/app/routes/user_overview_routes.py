from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.schemas.client_schema import ClientResponse
from app.schemas.companion_schema import CompanionResponse
from app.schemas.payment_schema import PaymentResponse
from app.schemas.product_schema import ProductResponse
from app.schemas.provider_payment_order_schema import ProviderPaymentOrderResponse
from app.schemas.provider_schema import ProviderResponse
from app.schemas.user_schema import UserResponse
from app.services.user_overview_service import UserOverviewService


class OverviewReservation(BaseModel):
    id_reserva: int
    codigo_reserva: str
    id_paquete_turistico: int
    paquete: str
    fecha_compra: Optional[datetime] = None
    fecha_reserva: date
    cantidad_personas: int
    total_reserva: Decimal
    estado: str
    fecha_cancelacion: Optional[datetime] = None
    penalidad_cancelacion: Optional[Decimal] = None
    reembolso: Optional[Decimal] = None
    acompanantes: List[CompanionResponse] = []


class OverviewNotification(BaseModel):
    id_notificacion_email: int
    asunto: str
    tipo_notificacion: str
    estado_envio: str
    fecha_envio: Optional[datetime] = None
    reservas_id_reserva: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OverviewSummary(BaseModel):
    reservas: int
    reservas_confirmadas: int
    total_pagado: Decimal
    penalidades: Decimal
    productos: int
    por_cobrar: Decimal
    cobrado: Decimal


class UserOverviewResponse(BaseModel):
    usuario: UserResponse
    cliente: Optional[ClientResponse] = None
    proveedor: Optional[ProviderResponse] = None
    reservas: List[OverviewReservation]
    pagos: List[PaymentResponse]
    productos: List[ProductResponse]
    ordenes_pago: List[ProviderPaymentOrderResponse]
    notificaciones: List[OverviewNotification]
    resumen: OverviewSummary


router = APIRouter(tags=["Users"])


@router.get("/users/{id_usuario}/overview", response_model=UserOverviewResponse)
def get_user_overview(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Ficha completa de un usuario (solo administradores)."""
    try:
        return UserOverviewService(db).get_overview(id_usuario, current_user)

    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))

    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))

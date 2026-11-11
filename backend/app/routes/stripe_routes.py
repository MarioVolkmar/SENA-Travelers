import json
import logging

import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.services import stripe_service
from app.services.stripe_service import StripeNotConfigured, StripeService

logger = logging.getLogger(__name__)

# Se registra antes que el router de /payments para que "/payments/{id}" no capture "stripe"
router = APIRouter(prefix="/payments/stripe", tags=["Payments · Stripe"])


class StripeCheckoutRequest(BaseModel):
    reserva_id: int = Field(..., gt=0)


class StripeConfirmRequest(BaseModel):
    session_id: str = Field(..., min_length=10, max_length=255)


def _http_error(error: Exception):
    if isinstance(error, StripeNotConfigured):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if isinstance(error, requests.RequestException):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No fue posible comunicarse con Stripe. Intenta de nuevo.")
    raise error


@router.get("/config")
def stripe_config():
    """Le dice al frontend si puede ofrecer el pago con Stripe."""
    return {"enabled": stripe_service.is_enabled(), "test_mode": stripe_service.is_test_mode()}


@router.post("/checkout")
def stripe_checkout(
    data: StripeCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return StripeService(db).checkout(data.reserva_id, current_user)
    except Exception as error:  # noqa: BLE001  (se traduce a un código HTTP)
        raise _http_error(error)


@router.post("/confirm")
def stripe_confirm(
    data: StripeConfirmRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return StripeService(db).confirm(data.session_id, current_user)
    except Exception as error:  # noqa: BLE001
        raise _http_error(error)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str | None = Header(default=None),
):
    """
    Webhook de Stripe (se configura en Desarrolladores → Webhooks).
    La firma se calcula sobre el cuerpo exacto, por eso se lee crudo antes de convertirlo.
    """
    payload = await request.body()
    try:
        event = json.loads(payload)
        return StripeService(db).handle_webhook(payload, stripe_signature or "", event)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except StripeNotConfigured as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    except (LookupError, ValueError) as error:
        # Aviso válido que no se puede aplicar: se responde 200 para que Stripe no lo reintente
        logger.warning("Aviso de Stripe no aplicado: %s", error)
        return {"applied": False, "detail": str(error)}

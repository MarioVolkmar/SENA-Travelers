from fastapi import APIRouter

from app.core.constants import IVA_PERCENT, LIMITS

router = APIRouter(prefix="/config", tags=["Configuración pública"])


@router.get("/limits")
def get_limits():
    """
    Límites de precios, cantidades y configuración (públicos, sin datos sensibles).
    El frontend los usa en sus formularios para validar con los mismos valores del backend.
    """
    return {"limites": LIMITS, "iva_porcentaje": IVA_PERCENT}

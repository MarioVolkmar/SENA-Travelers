"""
Desglose del IVA.

Los precios de Travelers incluyen el IVA (así lo exige el Estatuto del Consumidor), por eso
el impuesto se calcula hacia atrás desde el total:

    base sin IVA = total / (1 + 19 %)
    IVA          = total - base

Ejemplo: $1.190.000 → base $1.000.000 + IVA $190.000.
"""
from decimal import ROUND_HALF_UP, Decimal

from app.core.constants import IVA_PERCENT

CENT = Decimal("0.01")


def split_iva(total) -> tuple[Decimal, Decimal]:
    """(base sin IVA, IVA) de un valor que ya incluye el IVA. Siempre suman el total exacto."""
    total = Decimal(total or 0).quantize(CENT)
    base = (total / (1 + Decimal(IVA_PERCENT) / 100)).quantize(CENT, rounding=ROUND_HALF_UP)
    return base, total - base


def iva_of(total) -> Decimal:
    return split_iva(total)[1]


def base_of(total) -> Decimal:
    return split_iva(total)[0]

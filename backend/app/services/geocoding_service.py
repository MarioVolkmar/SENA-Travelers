"""
Ubica una ciudad en el mapa (latitud y longitud) con Nominatim, el buscador
gratuito de OpenStreetMap. No necesita llave de API.

Política de uso de Nominatim: identificarse con un User-Agent propio y no hacer
más de una consulta por segundo (aquí solo se consulta al crear o editar ciudades).
Se desactiva con GEOCODING_ENABLED=false (los tests lo hacen para no salir a internet).
"""
import logging
import os
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
TIMEOUT_SECONDS = 8


def geocoding_enabled() -> bool:
    return os.getenv("GEOCODING_ENABLED", "true").lower() == "true"


def _user_agent() -> str:
    site = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return f"Travelers-SENA/1.0 (+{site})"


def _search(params: dict):
    response = requests.get(
        NOMINATIM_URL,
        params={**params, "format": "jsonv2", "limit": 1, "accept-language": "es"},
        headers={"User-Agent": _user_agent()},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    first = results[0]
    return Decimal(first["lat"]).quantize(Decimal("0.000001")), Decimal(first["lon"]).quantize(Decimal("0.000001"))


def find_coordinates(nombre: str, departamento: str, pais: str = "Colombia"):
    """Devuelve (latitud, longitud) o None si no se encontró o el servicio falló."""
    if not geocoding_enabled():
        return None

    attempts = [
        {"city": nombre, "state": departamento, "country": pais},
        {"q": f"{nombre}, {departamento}, {pais}"},
        {"q": f"{nombre}, {pais}"},
    ]
    for params in attempts:
        try:
            found = _search(params)
        except (requests.RequestException, ValueError, KeyError):
            logger.warning("No se pudo consultar la ubicación de %s, %s", nombre, departamento, exc_info=True)
            return None
        if found:
            return found
    return None

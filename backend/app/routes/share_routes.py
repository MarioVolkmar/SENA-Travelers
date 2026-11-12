"""
Vista previa de los paquetes al compartir el enlace (WhatsApp, Facebook, Telegram, X...).

Esos robots no ejecutan JavaScript, así que la página de React no les muestra nada propio.
Nginx les envía /packages/{id} a este endpoint (solo a ellos, por su User-Agent), que
responde un HTML pequeño con las etiquetas Open Graph: foto, nombre y precio del paquete.
Si una persona llega aquí, el HTML la redirige a la página normal del paquete.
"""
from decimal import Decimal
from html import escape

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.constants import TOURIST_PACKAGE_STATUS_ACTIVE
from app.database.connection import get_db
from app.repositories.city_repository import CityRepository
from app.repositories.tourist_package_image_repository import TouristPackageImageRepository
from app.repositories.tourist_package_repository import TouristPackageRepository
from app.services.notification_email_service import frontend_url
from app.services.tourist_package_image_service import TouristPackageImageService

router = APIRouter(prefix="/share", tags=["Vista previa al compartir"])

SITE_NAME = "Travelers"
DEFAULT_TITLE = "Travelers · Paquetes turísticos por Colombia"
DEFAULT_DESCRIPTION = "Reserva paquetes turísticos por Colombia: alojamiento, tours y experiencias en un solo lugar."
MAX_DESCRIPTION = 180


def pesos(value) -> str:
    return f"${Decimal(value):,.0f}".replace(",", ".")


def short_text(text: str, limit: int = MAX_DESCRIPTION) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def render(title: str, description: str, image: str, url: str) -> str:
    title, description, image, url = (escape(value, quote=True) for value in (title, description, image, url))
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{SITE_NAME}" />
  <meta property="og:locale" content="es_CO" />
  <meta property="og:url" content="{url}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:image" content="{image}" />
  <meta property="og:image:alt" content="{title}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image" content="{image}" />
  <meta http-equiv="refresh" content="0; url={url}" />
</head>
<body>
  <p><a href="{url}">{title}</a></p>
</body>
</html>"""


@router.get("/packages/{id_paquete_turistico}", response_class=HTMLResponse)
def share_package(id_paquete_turistico: int, db: Session = Depends(get_db)):
    site = frontend_url()
    url = f"{site}/packages/{id_paquete_turistico}"
    default_image = f"{site}/og-image.jpg"

    package = TouristPackageRepository(db).find_by_id(id_paquete_turistico)
    if package is None or package.estado != TOURIST_PACKAGE_STATUS_ACTIVE:
        # Paquete que no existe o no está publicado: vista previa general del sitio
        return HTMLResponse(render(DEFAULT_TITLE, DEFAULT_DESCRIPTION, default_image, url))

    city = CityRepository(db).find_by_id(package.ciudad_id)
    cover = TouristPackageImageRepository(db).find_cover_by_package_id(id_paquete_turistico)
    image = (TouristPackageImageService.generate_image_url(cover.s3_key) if cover else None) or default_image

    price = Decimal(package.precio)
    if package.descuento:
        price = price - price * Decimal(package.descuento) / Decimal(100)

    title = f"{package.nombre} · {SITE_NAME}"
    place = f"{city.nombre} · " if city else ""
    offer = f" (−{package.descuento} %)" if package.descuento else ""
    description = short_text(
        f"{place}{pesos(price)} por persona, IVA incluido{offer}. {package.descripcion}"
    )
    return HTMLResponse(render(title, description, image, url))

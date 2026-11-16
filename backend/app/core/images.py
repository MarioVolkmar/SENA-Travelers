"""
Optimización de las fotos de los paquetes antes de subirlas a S3.

Las fotos de un celular o cámara pesan 3-6 MB y miden 4000+ px: demasiado para una página web.
Cada foto se guarda en dos tamaños, en JPEG progresivo y sin metadatos (EXIF, ubicación GPS):
  - grande:  máximo 1600 px de lado (detalle del paquete, banner, visor de fotos)
  - pequeña: máximo 800 px de lado (tarjetas, listas y miniaturas)
"""
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

LARGE_SIZE = 1600
SMALL_SIZE = 800
LARGE_QUALITY = 80
SMALL_QUALITY = 75


class InvalidImage(ValueError):
    pass


def _to_jpeg(image: Image.Image, max_side: int, quality: int) -> bytes:
    copy = image.copy()
    copy.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)  # nunca agranda
    output = BytesIO()
    copy.save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
    return output.getvalue()


def optimize_photo(data: bytes) -> tuple[bytes, bytes]:
    """Devuelve (grande, pequeña) en JPEG. Lanza InvalidImage si el archivo no es una imagen legible."""
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise InvalidImage("No se pudo leer la imagen. Usa una foto JPG, PNG o WEBP") from error

    image = ImageOps.exif_transpose(image)  # respeta la orientación con que se tomó la foto
    if image.mode in ("RGBA", "LA", "P"):
        # JPEG no tiene transparencia: se pone sobre fondo blanco
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    return _to_jpeg(image, LARGE_SIZE, LARGE_QUALITY), _to_jpeg(image, SMALL_SIZE, SMALL_QUALITY)

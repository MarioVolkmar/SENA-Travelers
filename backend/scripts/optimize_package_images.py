"""
Optimiza las fotos de paquetes que ya estaban subidas (las de antes de comprimir al subir).

Por cada foto sin versión pequeña:
  1. la descarga (desde CloudFront),
  2. la reduce y comprime en dos tamaños (app/core/images.py),
  3. sube los dos archivos nuevos a S3 con nombre único y caché de un año,
  4. actualiza la foto en la base para que apunte a los archivos nuevos.
Los archivos originales NO se borran del bucket (quedan como respaldo).
Se puede ejecutar varias veces: las fotos ya optimizadas se saltan.

Uso (desde la carpeta backend):
    python -m scripts.optimize_package_images            # optimiza
    python -m scripts.optimize_package_images --dry-run  # solo muestra cuánto se ahorraría
"""
import argparse
import importlib
import pkgutil
from uuid import uuid4

import requests

import app.models
from app.core import storage
from app.core.images import InvalidImage, optimize_photo
from app.database.connection import SessionLocal
from app.models.tourist_package_image_model import TouristPackageImageModel

# Todos los modelos deben estar cargados para que SQLAlchemy resuelva las relaciones al guardar
for module in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module.name}")


def main(dry_run: bool):
    db = SessionLocal()
    images = (
        db.query(TouristPackageImageModel)
        .filter(TouristPackageImageModel.s3_key_sm.is_(None))
        .order_by(TouristPackageImageModel.paquete_id, TouristPackageImageModel.orden)
        .all()
    )
    print(f"Fotos por optimizar: {len(images)}{' (simulación)' if dry_run else ''}")

    before_total = after_total = done = 0
    for image in images:
        url = storage.public_url(image.s3_key)
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            large, small = optimize_photo(response.content)
        except (requests.RequestException, InvalidImage) as error:
            print(f"  ! {image.s3_key}: no se pudo procesar ({error})")
            continue

        before, after = len(response.content), len(large)
        before_total += before
        after_total += after
        print(f"  {image.s3_key}: {before // 1024} KB -> {after // 1024} KB (miniatura {len(small) // 1024} KB)")
        if dry_run:
            continue

        name = uuid4().hex
        key, key_sm = f"{image.paquete_id}/{name}.jpg", f"{image.paquete_id}/{name}_sm.jpg"
        storage.upload_file(key, large, storage.IMAGE_CONTENT_TYPES["jpg"])
        storage.upload_file(key_sm, small, storage.IMAGE_CONTENT_TYPES["jpg"])
        image.s3_key, image.s3_key_sm = key, key_sm
        db.commit()
        done += 1

    if before_total:
        saved = 100 - after_total * 100 // before_total
        print(f"Total: {before_total / 1048576:.1f} MB -> {after_total / 1048576:.1f} MB ({saved} % menos)")
    print(f"Fotos actualizadas: {done}")
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="solo calcula el ahorro, no sube ni cambia nada")
    main(parser.parse_args().dry_run)

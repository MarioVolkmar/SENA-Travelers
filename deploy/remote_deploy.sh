#!/usr/bin/env bash
# Se ejecuta EN EL SERVIDOR (lo llama el pipeline de GitHub Actions por SSH).
#
# Recibe en /tmp/travelers-release/ dos paquetes: backend.tgz y frontend.tgz.
#   1. Guarda una copia de lo que está corriendo (para poder volver atrás).
#   2. Instala el backend nuevo, sus dependencias y aplica las migraciones (alembic upgrade head).
#   3. Reinicia el servicio y revisa que responda.
#   4. Publica el frontend nuevo.
# Si el backend no arranca, restaura la copia anterior y termina con error.
set -euo pipefail

APP=/opt/travelers
RELEASE=/tmp/travelers-release
BACKUPS=/home/ubuntu/deploy-backups
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="$BACKUPS/$STAMP"

mkdir -p "$BACKUP"
echo "==> Copia de respaldo en $BACKUP"
tar -czf "$BACKUP/backend.tgz" -C "$APP/backend" --exclude=venv --exclude=__pycache__ .
tar -czf "$BACKUP/frontend.tgz" -C "$APP/frontend" .
# Solo se guardan las 5 copias más recientes
ls -1dt "$BACKUPS"/*/ | tail -n +6 | xargs -r rm -rf

health() {
  for _ in $(seq 1 15); do
    if curl -fsS -o /dev/null http://127.0.0.1:8000/config/limits; then
      return 0
    fi
    sleep 2
  done
  return 1
}

rollback() {
  echo "!! El backend nuevo no respondió: restaurando la versión anterior"
  tar -xzf "$BACKUP/backend.tgz" -C "$APP/backend"
  sudo systemctl restart travelers
  health && echo "==> Versión anterior restaurada" || echo "!! Tampoco respondió la versión anterior: revisar a mano"
  exit 1
}

echo "==> Backend"
tar -xzf "$RELEASE/backend.tgz" -C "$APP/backend"
cd "$APP/backend"
venv/bin/pip install -q -r requirements.txt
venv/bin/alembic upgrade head
venv/bin/alembic current

sudo systemctl restart travelers
health || rollback
echo "==> Backend activo"

echo "==> Frontend"
rm -rf "$APP/frontend.new"
mkdir -p "$APP/frontend.new"
tar -xzf "$RELEASE/frontend.tgz" -C "$APP/frontend.new"
rm -rf "$APP/frontend.old"
mv "$APP/frontend" "$APP/frontend.old"
mv "$APP/frontend.new" "$APP/frontend"
rm -rf "$APP/frontend.old" "$RELEASE"

echo "==> Despliegue terminado ($STAMP)"

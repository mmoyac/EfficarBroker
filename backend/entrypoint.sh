#!/bin/sh
# Arranque del backend en producción:
#   1. espera a que Postgres acepte conexiones
#   2. aplica migraciones Alembic
#   3. siembra datos base (idempotente; controlable con SEED_ON_START)
#   4. lanza uvicorn con workers
set -e

echo "Esperando que PostgreSQL este listo..."
until pg_isready -h "${POSTGRES_HOST:-db}" -U "${POSTGRES_USER:-efficar}" >/dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL listo. Ejecutando migraciones..."
alembic upgrade head

if [ "${SEED_ON_START:-true}" = "true" ]; then
  echo "Sembrando datos base (idempotente)..."
  python -m src.seed
else
  echo "SEED_ON_START != true; se omite el seed."
fi

echo "Migraciones completadas. Iniciando aplicacion..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2

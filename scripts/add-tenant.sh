#!/bin/sh
# Da de alta un tenant en el nginx_proxy compartido del VPS.
# Uso (en el VPS):  ./add-tenant.sh <slug>
# Genera efficar-<slug>.effi4tech.cl a partir de la plantilla nginx-efficar.conf
# (que debe estar junto a este script) y recarga nginx.
set -e

SLUG="$1"
if [ -z "$SLUG" ]; then
  echo "Uso: $0 <slug>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="${TEMPLATE:-$SCRIPT_DIR/nginx-efficar.conf}"
DEST="/root/docker/nginx-proxy/conf.d/efficar-${SLUG}.conf"

if [ ! -f "$TEMPLATE" ]; then
  echo "Error: no se encuentra la plantilla $TEMPLATE" >&2
  exit 1
fi
if [ -f "$DEST" ]; then
  echo "Error: el tenant ya existe ($DEST)" >&2
  exit 1
fi

sed "s/TENANT_SLUG/${SLUG}/g" "$TEMPLATE" > "$DEST"

# Valida y recarga sin cortar el servicio.
docker exec nginx_proxy nginx -t && docker exec nginx_proxy nginx -s reload

echo "Tenant dado de alta: https://efficar-${SLUG}.effi4tech.cl"
echo "Recuerda crear el tenant en la BD si es distinto de 'vendemostuautomovil' (ya sembrado)."

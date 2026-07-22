"""Identidad de app PWA host-aware (sin auth).

Sirve el `manifest.webmanifest` y los iconos según el dominio de la petición
(`Host` → `Tenant.dominio`), de modo que un único build de frontend, servido
por múltiples dominios, presente el nombre e icono de la automotora
correspondiente al instalarse. Si el host no mapea a ningún tenant, cae a la
identidad por defecto de la plataforma (no 404: la app debe seguir siendo
instalable en dev/staging).

Estas rutas van montadas SIN el prefijo `/api/v1`: el manifest y los iconos
deben vivir en rutas estables del mismo origen que la página.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Response

from src.config import settings
from src.dependencies import get_tenant_by_host
from src.models.tenant import Tenant
from src.services import app_icons

router = APIRouter(tags=["pwa"])

# Cache corta y revalidable: el icono/nombre depende del tenant y puede cambiar
# (p. ej. si actualiza su logo), así que no se marca inmutable.
_CACHE = "public, max-age=300, must-revalidate"

_ICON_ROUTES = {
    "icon-192.png": (192, False),
    "icon-512.png": (512, False),
    "maskable-192.png": (192, True),
    "maskable-512.png": (512, True),
    "apple-touch-icon.png": (180, False),
}


@router.get("/manifest.webmanifest", include_in_schema=False)
def manifest(tenant: Tenant | None = Depends(get_tenant_by_host)) -> Response:
    nombre = tenant.nombre if tenant else settings.PWA_APP_NAME
    data = {
        "name": nombre,
        "short_name": nombre[:12].strip(),
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "theme_color": settings.PWA_THEME_COLOR,
        "background_color": settings.PWA_BACKGROUND_COLOR,
        "icons": [
            {"src": "/app-icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/app-icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/app-icons/maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "/app-icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return Response(
        content=json.dumps(data, ensure_ascii=False),
        media_type="application/manifest+json",
        headers={"Cache-Control": _CACHE},
    )


@router.get("/app-icons/{filename}", include_in_schema=False)
def app_icon(
    filename: str,
    tenant: Tenant | None = Depends(get_tenant_by_host),
) -> Response:
    spec = _ICON_ROUTES.get(filename)
    if spec is None:
        return Response(status_code=404)
    size, maskable = spec
    if tenant is not None:
        png = app_icons.render_tenant_icon(tenant, size, maskable)
    else:
        png = app_icons.render_default_icon(size, maskable)
    return Response(content=png, media_type="image/png", headers={"Cache-Control": _CACHE})

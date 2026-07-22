"""Storage de archivos de la galería (fotos subidas).

Implementación de filesystem local: guarda cada archivo bajo
`MEDIA_ROOT/<tenant_id>/<uuid>.<ext>` y devuelve la URL servible
(`MEDIA_URL_BASE/<tenant_id>/<uuid>.<ext>`), que `main.py` monta con StaticFiles.

El contrato (bytes -> URL, y borrar por URL) es idéntico al que tendría un
backend S3/objeto: migrar después es reimplementar estas dos funciones, sin
tocar el modelo ni la API.
"""

import uuid
from pathlib import Path

from src.config import settings

# Extensión servible por cada MIME aceptado.
_EXT_POR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def ext_para_mime(content_type: str | None) -> str | None:
    """Extensión asociada a un MIME de imagen soportado, o None si no lo es."""
    if content_type is None:
        return None
    return _EXT_POR_MIME.get(content_type.split(";")[0].strip().lower())


def save(tenant_id: int, content: bytes, ext: str) -> str:
    """Guarda `content` para el tenant y devuelve la URL servible."""
    tenant_dir = Path(settings.MEDIA_ROOT) / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}{ext}"
    (tenant_dir / nombre).write_bytes(content)
    return f"{settings.MEDIA_URL_BASE}/{tenant_id}/{nombre}"


def _es_url_local(url: str) -> bool:
    return url.startswith(f"{settings.MEDIA_URL_BASE}/")


def delete(url: str) -> None:
    """Borra el archivo local de una URL de storage propio. Las URLs externas
    (cloud) no se tocan: no son nuestras. Silencioso si el archivo no existe."""
    if not _es_url_local(url):
        return
    rel = url[len(settings.MEDIA_URL_BASE) :].lstrip("/")
    ruta = (Path(settings.MEDIA_ROOT) / rel).resolve()
    root = Path(settings.MEDIA_ROOT).resolve()
    # Defensa ante path traversal: solo se borra dentro de MEDIA_ROOT.
    if root not in ruta.parents:
        return
    ruta.unlink(missing_ok=True)

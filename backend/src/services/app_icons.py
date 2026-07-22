"""Generación de iconos PWA por tenant, derivados de su logo.

Toma el `logo` del tenant (data-URI o URL http), lo normaliza a un PNG
cuadrado (con fondo y, para la variante `maskable`, padding de zona segura) y
lo cachea en disco por tenant + tamaño + variante + hash del logo. Si el tenant
no tiene logo (o falla su carga), genera un icono por defecto con las iniciales
sobre el fondo de marca.

Punto de extensión (override futuro): cuando exista un asset de icono dedicado
por tenant, `_source_image` debe priorizarlo sobre el logo, sin cambiar el
contrato de estas funciones ni las URLs que consume el manifest/HTML.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from src.config import settings
from src.models.tenant import Tenant

_BRAND_ACCENT = (255, 215, 1, 255)  # #FFD701
_BRAND_INK = (34, 39, 50, 255)  # #222732
_WHITE = (255, 255, 255, 255)

# Fracción del lienzo ocupada por el contenido útil. `maskable` deja más margen
# porque el SO recorta el icono a distintas formas (círculo, squircle…).
_SAFE_MASKABLE = 0.80
_SAFE_NORMAL = 0.92


def _cache_dir() -> Path:
    d = Path(settings.PWA_ICON_CACHE_ROOT)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _iniciales(nombre: str) -> str:
    partes = [p for p in nombre.strip().split() if p]
    if not partes:
        return "EC"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def _load_logo_image(logo: str) -> Image.Image | None:
    """Carga el logo (data-URI o URL http) como imagen RGBA; None si falla."""
    try:
        if logo.startswith("data:"):
            _, _, b64 = logo.partition(",")
            data = base64.b64decode(b64, validate=False)
        elif logo.startswith(("http://", "https://")):
            resp = httpx.get(logo, timeout=10.0, follow_redirects=True)
            resp.raise_for_status()
            data = resp.content
        else:
            return None
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except (httpx.HTTPError, binascii.Error, OSError, ValueError):
        return None


def _source_image(tenant: Tenant) -> Image.Image | None:
    """Imagen fuente del icono del tenant. Override futuro: priorizar aquí un
    asset de icono dedicado antes de caer al logo."""
    if tenant.logo:
        return _load_logo_image(tenant.logo)
    return None


def _fit_on_canvas(logo_img: Image.Image, size: int, maskable: bool) -> Image.Image:
    """Compone el logo centrado sobre un lienzo cuadrado con fondo blanco,
    escalado dentro de la zona segura y respetando su transparencia."""
    canvas = Image.new("RGBA", (size, size), _WHITE)
    box = int(size * (_SAFE_MASKABLE if maskable else _SAFE_NORMAL))
    # Escala (arriba o abajo) para llenar la zona segura manteniendo proporción.
    scale = box / max(logo_img.width, logo_img.height)
    new_size = (max(1, round(logo_img.width * scale)), max(1, round(logo_img.height * scale)))
    logo = logo_img.resize(new_size, Image.LANCZOS)
    off = ((size - logo.width) // 2, (size - logo.height) // 2)
    canvas.paste(logo, off, logo)
    return canvas


def _brand_icon(label: str, size: int) -> Image.Image:
    """Icono por defecto: iniciales sobre fondo de marca. Sin dependencia de
    fuentes del sistema (la imagen base es python-slim): si no hay TrueType
    escalable, cae a un cuadrado de marca liso."""
    img = Image.new("RGBA", (size, size), _BRAND_ACCENT)
    text = _iniciales(label)
    draw = ImageDraw.Draw(img)
    try:
        try:
            font = ImageFont.load_default(size=int(size * 0.42))
        except TypeError:  # Pillow < 10 no acepta size
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos = ((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1])
        draw.text(pos, text, fill=_BRAND_INK, font=font)
    except OSError:
        pass  # sin fuente utilizable: queda el cuadrado de marca liso
    return img


def _encode(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _variant(size: int, maskable: bool) -> str:
    return f"maskable-{size}" if maskable else f"icon-{size}"


def render_tenant_icon(tenant: Tenant, size: int, maskable: bool = False) -> bytes:
    """PNG del icono del tenant al tamaño/variante pedidos, cacheado en disco."""
    raw_sig = (tenant.logo or f"__initials__:{tenant.nombre}").encode("utf-8")
    sig = hashlib.sha256(raw_sig).hexdigest()[:16]
    cache = _cache_dir() / f"tenant-{tenant.id}-{_variant(size, maskable)}-{sig}.png"
    if cache.exists():
        return cache.read_bytes()

    src = _source_image(tenant)
    img = _fit_on_canvas(src, size, maskable) if src is not None else _brand_icon(tenant.nombre, size)
    data = _encode(img)
    cache.write_bytes(data)
    return data


def render_default_icon(size: int, maskable: bool = False) -> bytes:
    """Icono por defecto de la plataforma (host no mapeado a ningún tenant)."""
    cache = _cache_dir() / f"default-{_variant(size, maskable)}.png"
    if cache.exists():
        return cache.read_bytes()
    data = _encode(_brand_icon(settings.PWA_APP_NAME, size))
    cache.write_bytes(data)
    return data

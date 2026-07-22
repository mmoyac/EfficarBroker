"""Validación y normalización de enlaces de video de YouTube.

Acepta las tres formas de URL de YouTube (watch, corta y shorts), extrae el id
del video y devuelve una URL canónica. Cualquier otro dominio se rechaza para no
guardar enlaces arbitrarios en un campo pensado solo para el video 360.
"""

import re
from urllib.parse import parse_qs, urlparse

_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extraer_video_id(url: str) -> str | None:
    """Devuelve el id de 11 caracteres si `url` es de YouTube, o None."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.")

    if host in {"youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            vid = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            vid = parsed.path.split("/shorts/", 1)[1].split("/")[0]
        elif parsed.path.startswith("/embed/"):
            vid = parsed.path.split("/embed/", 1)[1].split("/")[0]
        else:
            vid = None
    elif host == "youtu.be":
        vid = parsed.path.lstrip("/").split("/")[0]
    else:
        vid = None

    return vid if vid and _ID.match(vid) else None


def normalizar(url: str) -> str | None:
    """URL canónica `https://www.youtube.com/watch?v=<id>` o None si no es válida."""
    vid = extraer_video_id(url)
    return f"https://www.youtube.com/watch?v={vid}" if vid else None

"""Utilidades de seguridad: hashing de passwords y emisión/validación de JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN = "access"
REFRESH_TOKEN = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    *, user_id: int, tenant_id: int | None, role: str, active_tenant_id: int | None = None
) -> str:
    extra: dict[str, Any] = {"tenant_id": tenant_id, "role": role}
    # Solo se incluye el claim cuando el SuperAdmin ha seleccionado un tenant activo.
    if active_tenant_id is not None:
        extra["active_tenant_id"] = active_tenant_id
    return _create_token(
        subject=str(user_id),
        token_type=ACCESS_TOKEN,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra=extra,
    )


def create_refresh_token(*, user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        token_type=REFRESH_TOKEN,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un JWT. Lanza jwt.PyJWTError si es inválido/expirado."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

"""Dependencies compartidas: autenticación, contexto de tenant y RBAC."""

from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import User
from src.utils.security import ACCESS_TOKEN, decode_token

bearer_scheme = HTTPBearer(auto_error=False)

SUPERADMIN = "SuperAdmin"


@dataclass
class TenantContext:
    """Contexto de tenant derivado EXCLUSIVAMENTE del token (no del cliente).

    - tenant_id: tenant EFECTIVO (para no-SuperAdmin, el suyo; para SuperAdmin,
      el `active_tenant_id` seleccionado, o None en vista plataforma).
    - is_platform: True si el usuario es SuperAdmin (dueño de plataforma).
    - active_tenant_id: tenant activo seleccionado por el SuperAdmin (o None).
    """

    tenant_id: int | None
    is_platform: bool
    active_tenant_id: int | None


_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_EXC
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC
    if payload.get("type") != ACCESS_TOKEN:
        raise _CREDENTIALS_EXC
    return payload


def get_current_user(
    claims: dict[str, Any] = Depends(get_current_claims),
    db: Session = Depends(get_db),
) -> User:
    user_id = claims.get("sub")
    if user_id is None:
        raise _CREDENTIALS_EXC
    user = db.get(User, int(user_id))
    if user is None or not user.activo:
        raise _CREDENTIALS_EXC
    return user


def get_current_tenant(
    user: User = Depends(get_current_user),
    claims: dict[str, Any] = Depends(get_current_claims),
) -> TenantContext:
    """Resuelve el tenant efectivo. El SuperAdmin puede operar dentro de un
    tenant activo (claim `active_tenant_id`) o en vista plataforma (None)."""
    is_platform = user.role.code == SUPERADMIN
    if is_platform:
        active = claims.get("active_tenant_id")
        return TenantContext(tenant_id=active, is_platform=True, active_tenant_id=active)
    return TenantContext(tenant_id=user.tenant_id, is_platform=False, active_tenant_id=None)


def get_effective_tenant_id(ctx: TenantContext = Depends(get_current_tenant)) -> int:
    """Tenant efectivo obligatorio para endpoints transaccionales. Si un
    SuperAdmin no ha seleccionado tenant activo, se exige seleccionar uno."""
    if ctx.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Selecciona un tenant activo para operar sobre sus datos.",
        )
    return ctx.tenant_id


def require_roles(*roles: str):
    """Genera una dependency que exige que el rol del usuario esté en `roles`."""

    def _guard(user: User = Depends(get_current_user)) -> User:
        # SuperAdmin es transversal: siempre autorizado.
        if user.role.code == SUPERADMIN:
            return user
        if user.role.code not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para este recurso",
            )
        return user

    return _guard

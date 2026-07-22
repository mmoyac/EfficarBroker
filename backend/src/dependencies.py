"""Dependencies compartidas: autenticación, contexto de tenant y RBAC."""

from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.models.tenant import Tenant
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


def get_tenant_by_host(
    request: Request,
    db: Session = Depends(get_db),
) -> Tenant | None:
    """Resuelve el tenant a partir del dominio de la petición (host-aware).

    Usado por endpoints PÚBLICOS sin auth (manifest/iconos PWA): el `tenant_id`
    no viene del JWT sino del dominio por el que entra el navegador. Devuelve None
    si el host no mapea a ningún tenant activo → el llamador cae a la identidad por
    defecto de la plataforma.

    Dos formas de resolución:
    1. **Backoffice** (caso real de prod): el host es `efficar-<slug>.effi4tech.cl`
       (`APP_HOST_PREFIX`/`APP_HOST_SUFFIX`). Se extrae el `slug` y se busca
       `Tenant.slug`. La app es la misma para todos los tenants sobre distintos
       subdominios; el slug es la clave por-tenant del backoffice.
    2. **Dominio público** (para el futuro catálogo): match directo `Tenant.dominio`
       (la landing .com del tenant), distinto del subdominio del backoffice.

    En producción el front está detrás de nginx, que reenvía el dominio real en
    `Host` (`proxy_set_header Host $host`); se contempla `X-Forwarded-Host` por si
    hubiera un proxy intermedio.
    """
    raw = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    # Primer host de la lista, sin puerto, en minúsculas.
    host = raw.split(",")[0].strip().split(":")[0].lower()
    if not host:
        return None

    # 1) Backoffice: efficar-<slug>.effi4tech.cl -> Tenant.slug
    prefix = settings.APP_HOST_PREFIX.lower()
    suffix = settings.APP_HOST_SUFFIX.lower()
    if host.startswith(prefix) and host.endswith(suffix):
        slug = host[len(prefix) : len(host) - len(suffix)]
        if slug:
            tenant = db.scalars(
                select(Tenant).where(Tenant.slug == slug, Tenant.activo.is_(True))
            ).one_or_none()
            if tenant is not None:
                return tenant

    # 2) Dominio público de la landing (.com) -> Tenant.dominio
    return db.scalars(
        select(Tenant).where(Tenant.dominio == host, Tenant.activo.is_(True))
    ).one_or_none()


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

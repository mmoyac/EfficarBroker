from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import SUPERADMIN, get_current_claims, get_current_user, require_roles
from src.models.tenant import Tenant
from src.models.user import User
from src.schemas.auth import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    SelectTenantRequest,
    TokenPair,
    UserMe,
)
from src.utils.security import (
    REFRESH_TOKEN,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == body.email))
    # Mensaje genérico: no revela si el email existe.
    if user is None or not user.activo or not verify_password(body.password, user.password_hash):
        raise _INVALID_CREDENTIALS
    return TokenPair(
        access_token=create_access_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role.code
        ),
        refresh_token=create_refresh_token(user_id=user.id),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> AccessToken:
    try:
        payload = decode_token(body.refresh_token)
    except jwt.PyJWTError:
        raise _INVALID_CREDENTIALS
    if payload.get("type") != REFRESH_TOKEN:
        raise _INVALID_CREDENTIALS

    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id is not None else None
    if user is None or not user.activo:
        raise _INVALID_CREDENTIALS

    return AccessToken(
        access_token=create_access_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role.code
        )
    )


@router.get("/me", response_model=UserMe)
def me(
    user: User = Depends(get_current_user),
    claims: dict[str, Any] = Depends(get_current_claims),
    db: Session = Depends(get_db),
) -> UserMe:
    active_id: int | None = None
    active_name: str | None = None
    if user.role.code == SUPERADMIN:
        active_id = claims.get("active_tenant_id")
        if active_id is not None:
            active = db.get(Tenant, active_id)
            active_name = active.nombre if active else None
    return UserMe(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        telefono=user.telefono,
        role=user.role.nombre,
        role_code=user.role.code,
        tenant_id=user.tenant_id,
        tenant=user.tenant.nombre if user.tenant else None,
        sucursal_id=user.sucursal_id,
        active_tenant_id=active_id,
        active_tenant=active_name,
    )


@router.post("/select-tenant", response_model=AccessToken)
def select_tenant(
    body: SelectTenantRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(SUPERADMIN)),
) -> AccessToken:
    """El SuperAdmin fija un tenant activo. Se re-emite un access token con el
    claim `active_tenant_id`. El tenant efectivo pasa a ser el seleccionado."""
    tenant = db.get(Tenant, body.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    if not tenant.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant inactivo")
    return AccessToken(
        access_token=create_access_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role.code,
            active_tenant_id=tenant.id,
        )
    )


@router.post("/exit-tenant", response_model=AccessToken)
def exit_tenant(user: User = Depends(require_roles(SUPERADMIN))) -> AccessToken:
    """El SuperAdmin vuelve a la vista de plataforma (token sin tenant activo)."""
    return AccessToken(
        access_token=create_access_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role.code
        )
    )

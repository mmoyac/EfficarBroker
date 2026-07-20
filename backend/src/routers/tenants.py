from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import SUPERADMIN, get_effective_tenant_id, require_roles
from src.models.tenant import Tenant
from src.schemas.tenant import TenantOut, TenantUpdate
from src.services.user_service import count_active_users

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _to_out(db: Session, tenant: Tenant) -> TenantOut:
    return TenantOut(
        id=tenant.id,
        nombre=tenant.nombre,
        dominio=tenant.dominio,
        activo=tenant.activo,
        max_usuarios=tenant.max_usuarios,
        usuarios_activos=count_active_users(db, tenant.id),
    )


@router.get("", response_model=list[TenantOut])
def list_tenants(
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> list[TenantOut]:
    """Directorio de tenants (con uso de cupo) para el SuperAdmin."""
    tenants = db.scalars(select(Tenant).order_by(Tenant.nombre)).all()
    return [_to_out(db, t) for t in tenants]


@router.get("/current", response_model=TenantOut)
def current_tenant(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    _=Depends(require_roles("TenantAdmin")),
) -> TenantOut:
    """Tenant efectivo actual (con uso de cupo). Accesible al TenantAdmin para
    ver su propio límite sin poder listar los demás tenants."""
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return _to_out(db, tenant)


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant_quota(
    tenant_id: int,
    body: TenantUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> TenantOut:
    """Fija el cupo de usuarios del tenant. Solo SuperAdmin. NULL = ilimitado."""
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    if body.max_usuarios is not None and body.max_usuarios < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cupo inválido")
    tenant.max_usuarios = body.max_usuarios
    db.commit()
    db.refresh(tenant)
    return _to_out(db, tenant)

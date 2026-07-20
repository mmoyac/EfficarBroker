"""Lógica de negocio de usuarios y cupo de licencias por tenant."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.tenant import Tenant
from src.models.user import User


def count_active_users(db: Session, tenant_id: int) -> int:
    return db.scalar(
        select(func.count(User.id)).where(User.tenant_id == tenant_id, User.activo.is_(True))
    ) or 0


def ensure_quota_available(db: Session, tenant_id: int) -> None:
    """Verifica que el tenant no haya alcanzado su cupo de usuarios activos.

    `max_usuarios = NULL` significa ilimitado. Lanza 409 si el cupo se alcanzó.
    """
    tenant = db.get(Tenant, tenant_id)
    if tenant is None or tenant.max_usuarios is None:
        return
    if count_active_users(db, tenant_id) >= tenant.max_usuarios:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Se alcanzó el límite de usuarios del plan ({tenant.max_usuarios}). "
                "Contacte a la plataforma para ampliar el cupo."
            ),
        )

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Timestamps de creación/actualización gestionados por el servidor."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantMixin:
    """Mixin de aislamiento multitenant: FK obligatoria a tenants.

    Toda tabla transaccional (maestra u operacional, salvo la propia `tenants`
    y los catálogos globales de plataforma) hereda este mixin. Las consultas
    SIEMPRE deben filtrar por `tenant_id` del usuario autenticado.
    """

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), index=True, nullable=False
    )

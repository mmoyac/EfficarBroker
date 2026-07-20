"""Tabla OPERACIONAL: logs_auditoria (append-only).

estado_anterior / estado_nuevo se guardan como snapshot de texto inmutable
(patrón de auditoría), además de existir el catálogo estados_vehiculo.
La inmutabilidad (rechazo de UPDATE/DELETE) se refuerza con un trigger de
PostgreSQL creado en la migración inicial.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    # tenant_id nullable para permitir eventos de plataforma (SuperAdmin)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entidad: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(80), nullable=True)
    estado_nuevo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

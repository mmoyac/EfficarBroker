"""Servicio de auditoría append-only.

Inserta filas inmutables en logs_auditoria. Solo expone la operación de escritura
(INSERT); nunca UPDATE/DELETE. La BD refuerza la inmutabilidad con un trigger.
"""

from sqlalchemy.orm import Session

from src.models.audit import LogAuditoria


def log(
    db: Session,
    *,
    tenant_id: int | None,
    user_id: int | None,
    ip: str | None = None,
    entidad: str | None = None,
    entidad_id: int | None = None,
    estado_anterior: str | None = None,
    estado_nuevo: str | None = None,
    payload: dict | None = None,
) -> LogAuditoria:
    entry = LogAuditoria(
        tenant_id=tenant_id,
        user_id=user_id,
        ip=ip,
        entidad=entidad,
        entidad_id=entidad_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        payload=payload,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

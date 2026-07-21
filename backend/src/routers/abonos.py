"""Resumen financiero de los abonos de exclusividad.

Separa el dinero ya ganado por la empresa del todavía comprometido, base para
el dashboard financiero futuro. El abono es un ANTICIPO de comisión: mientras el
acta está vigente (NO_DEVENGADO) es dinero cobrado pero no devengado; al
resolverse (APLICADO_COMISION o RETENIDO) se reconoce como ingreso.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_effective_tenant_id, require_roles
from src.models.acta import ActaRecepcion
from src.models.catalogs import EstadoAbono
from src.schemas.acta import AbonoResumenItemOut, AbonoResumenOut

router = APIRouter(prefix="/abonos", tags=["abonos"])

# Cifras financieras: solo gestión y administración.
_guard = Depends(require_roles("Management", "TenantAdmin", "SuperAdmin"))

NO_DEVENGADO = "NO_DEVENGADO"


@router.get("/resumen", response_model=AbonoResumenOut, dependencies=[_guard])
def resumen_abonos(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    sucursal_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> AbonoResumenOut:
    stmt = (
        select(
            EstadoAbono.code,
            EstadoAbono.nombre,
            func.coalesce(func.sum(ActaRecepcion.exclusividad_abono), 0),
            func.count(ActaRecepcion.id),
        )
        .join(EstadoAbono, EstadoAbono.id == ActaRecepcion.estado_abono_id)
        .where(ActaRecepcion.tenant_id == tenant_id)
        .group_by(EstadoAbono.code, EstadoAbono.nombre, EstadoAbono.id)
        .order_by(EstadoAbono.id)
    )
    if desde is not None:
        stmt = stmt.where(ActaRecepcion.fecha_recepcion >= desde)
    if hasta is not None:
        stmt = stmt.where(ActaRecepcion.fecha_recepcion <= hasta)
    if sucursal_id is not None:
        stmt = stmt.where(ActaRecepcion.sucursal_id == sucursal_id)

    detalle: list[AbonoResumenItemOut] = []
    comprometido = 0
    ganado = 0
    for code, nombre, total, cantidad in db.execute(stmt).all():
        total = int(total)
        detalle.append(AbonoResumenItemOut(
            estado_code=code, estado=nombre, total=total, cantidad=int(cantidad)
        ))
        if code == NO_DEVENGADO:
            comprometido += total
        else:
            ganado += total

    return AbonoResumenOut(comprometido=comprometido, ganado=ganado, detalle=detalle)

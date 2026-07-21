"""Comisiones del ejecutivo, parámetros, liquidación y estado de resultados."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user, get_effective_tenant_id, require_roles
from src.models.acta import ActaRecepcion
from src.models.catalogs import EstadoAbono, EstadoPagoComision, EstadoVehiculo
from src.models.comision import ComisionEjecutivo, OrdenPago, ParametrosComision
from src.models.user import User
from src.schemas.comision import (
    ComisionesResumenOut,
    ComisionOut,
    EstadoResultadoOut,
    OrdenPagoCreate,
    OrdenPagoOut,
    ParametrosComisionIn,
    ParametrosComisionOut,
)
from src.services import audit_service
from src.utils.comision import calcular_comision

router = APIRouter(tags=["comisiones"])

_ROLES_TRANSVERSALES = ("Management", "TenantAdmin", "SuperAdmin")
_guard_ver = Depends(require_roles("Sales", "Management", "TenantAdmin"))
_guard_admin = Depends(require_roles("TenantAdmin"))
_guard_liq = Depends(require_roles("Management", "TenantAdmin", "SuperAdmin"))


def _params(db: Session, tenant_id: int) -> ParametrosComision:
    p = db.scalar(select(ParametrosComision).where(ParametrosComision.tenant_id == tenant_id))
    if p is None:
        p = ParametrosComision(tenant_id=tenant_id, pool_pct=20, captacion_pct=40, venta_pct=60)
        db.add(p)
        db.commit()
        db.refresh(p)
    return p


def _comision_out(c: ComisionEjecutivo) -> ComisionOut:
    v = c.acta.vehiculo
    return ComisionOut(
        id=c.id, acta_id=c.acta_id, ppu=v.ppu,
        vehiculo=f"{v.marca_nombre} {v.modelo_nombre}",
        cliente=c.acta.cliente.nombre, beneficiario=c.beneficiario.nombre,
        tipo=c.tipo.nombre, tipo_code=c.tipo.code,
        monto=c.monto, estado_pago=c.estado_pago.nombre, estado_pago_code=c.estado_pago.code,
        fecha_generacion=c.fecha_generacion, orden_pago_id=c.orden_pago_id,
        fecha_venta=c.acta.fecha_venta,
    )


# ---------------------------------------------------------------- parámetros


@router.get("/parametros-comision", response_model=ParametrosComisionOut, dependencies=[_guard_ver])
def obtener_parametros(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> ParametrosComisionOut:
    return ParametrosComisionOut.model_validate(_params(db, tenant_id))


@router.patch("/parametros-comision", response_model=ParametrosComisionOut, dependencies=[_guard_admin])
def editar_parametros(
    body: ParametrosComisionIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ParametrosComisionOut:
    if body.captacion_pct + body.venta_pct != 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El split captación + venta debe sumar 100.",
        )
    p = _params(db, tenant_id)
    p.pool_pct = body.pool_pct
    p.captacion_pct = body.captacion_pct
    p.venta_pct = body.venta_pct
    db.flush()
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="parametros_comision", entidad_id=p.id,
        estado_anterior=None, estado_nuevo=None,
        payload={"accion": "editar_parametros_comision",
                 "pool_pct": p.pool_pct, "captacion_pct": p.captacion_pct, "venta_pct": p.venta_pct},
    )
    db.refresh(p)
    return ParametrosComisionOut.model_validate(p)


# ---------------------------------------------------------------- comisiones


@router.get("/comisiones", response_model=ComisionesResumenOut, dependencies=[_guard_ver])
def listar_comisiones(
    mine: bool = False,
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    estado_pago: str | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ComisionesResumenOut:
    stmt = select(ComisionEjecutivo).where(ComisionEjecutivo.tenant_id == tenant_id)
    # Sales solo ve lo suyo; los transversales ven todo salvo que pidan ?mine.
    if mine or current.role.code not in _ROLES_TRANSVERSALES:
        stmt = stmt.where(ComisionEjecutivo.beneficiario_user_id == current.id)
    if estado_pago:
        stmt = stmt.join(EstadoPagoComision, EstadoPagoComision.id == ComisionEjecutivo.estado_pago_id).where(
            EstadoPagoComision.code == estado_pago.upper()
        )
    comisiones = list(db.scalars(stmt.order_by(ComisionEjecutivo.fecha_generacion.desc())).all())
    # Filtro por fecha de venta del acta (en Python; volumen bajo).
    if desde is not None:
        comisiones = [c for c in comisiones if c.acta.fecha_venta and c.acta.fecha_venta >= desde]
    if hasta is not None:
        comisiones = [c for c in comisiones if c.acta.fecha_venta and c.acta.fecha_venta <= hasta]

    items = [_comision_out(c) for c in comisiones]
    total = sum(c.monto for c in comisiones)
    pend = sum(c.monto for c in comisiones if c.estado_pago.code == "PENDIENTE")
    pag = sum(c.monto for c in comisiones if c.estado_pago.code == "PAGADA")
    return ComisionesResumenOut(total=total, total_pendiente=pend, total_pagada=pag, items=items)


# ---------------------------------------------------------------- órdenes de pago


@router.post("/ordenes-pago", response_model=OrdenPagoOut, status_code=status.HTTP_201_CREATED, dependencies=[_guard_liq])
def crear_orden_pago(
    body: OrdenPagoCreate,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> OrdenPagoOut:
    beneficiario = db.get(User, body.beneficiario_user_id)
    if beneficiario is None or beneficiario.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Beneficiario inválido")
    if body.periodo_desde > body.periodo_hasta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Período inválido")

    pagada = db.scalar(select(EstadoPagoComision).where(EstadoPagoComision.code == "PAGADA"))

    # Comisiones PENDIENTE del beneficiario cuya venta cae en el período.
    candidatas = db.scalars(
        select(ComisionEjecutivo)
        .join(EstadoPagoComision, EstadoPagoComision.id == ComisionEjecutivo.estado_pago_id)
        .where(
            ComisionEjecutivo.tenant_id == tenant_id,
            ComisionEjecutivo.beneficiario_user_id == beneficiario.id,
            EstadoPagoComision.code == "PENDIENTE",
        )
    ).all()
    incluidas = [
        c for c in candidatas
        if c.acta.fecha_venta and body.periodo_desde <= c.acta.fecha_venta <= body.periodo_hasta
    ]

    monto_comisiones = sum(c.monto for c in incluidas)
    orden = OrdenPago(
        tenant_id=tenant_id, beneficiario_user_id=beneficiario.id,
        periodo_desde=body.periodo_desde, periodo_hasta=body.periodo_hasta,
        fecha_pago=body.fecha_pago, monto_comisiones=monto_comisiones,
        monto_base=body.monto_base, monto_total=monto_comisiones + body.monto_base,
    )
    db.add(orden)
    db.flush()
    for c in incluidas:
        c.orden_pago_id = orden.id
        c.estado_pago_id = pagada.id
    db.flush()
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="orden_pago", entidad_id=orden.id,
        estado_anterior=None, estado_nuevo="PAGADA",
        payload={"accion": "crear_orden_pago", "beneficiario_id": beneficiario.id,
                 "comisiones": [c.id for c in incluidas], "monto_total": orden.monto_total},
    )
    db.refresh(orden)
    return OrdenPagoOut(
        id=orden.id, beneficiario=beneficiario.nombre, beneficiario_user_id=beneficiario.id,
        periodo_desde=orden.periodo_desde, periodo_hasta=orden.periodo_hasta,
        fecha_pago=orden.fecha_pago, monto_comisiones=orden.monto_comisiones,
        monto_base=orden.monto_base, monto_total=orden.monto_total,
        comisiones=[_comision_out(c) for c in incluidas],
    )


@router.get("/ordenes-pago", response_model=list[OrdenPagoOut], dependencies=[_guard_ver])
def listar_ordenes_pago(
    mine: bool = False,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> list[OrdenPagoOut]:
    stmt = select(OrdenPago).where(OrdenPago.tenant_id == tenant_id)
    if mine or current.role.code not in _ROLES_TRANSVERSALES:
        stmt = stmt.where(OrdenPago.beneficiario_user_id == current.id)
    ordenes = db.scalars(stmt.order_by(OrdenPago.fecha_pago.desc(), OrdenPago.id.desc())).all()
    out: list[OrdenPagoOut] = []
    for o in ordenes:
        comisiones = db.scalars(
            select(ComisionEjecutivo).where(ComisionEjecutivo.orden_pago_id == o.id)
        ).all()
        out.append(OrdenPagoOut(
            id=o.id, beneficiario=o.beneficiario.nombre, beneficiario_user_id=o.beneficiario_user_id,
            periodo_desde=o.periodo_desde, periodo_hasta=o.periodo_hasta, fecha_pago=o.fecha_pago,
            monto_comisiones=o.monto_comisiones, monto_base=o.monto_base, monto_total=o.monto_total,
            comisiones=[_comision_out(c) for c in comisiones],
        ))
    return out


# ---------------------------------------------------------------- estado de resultados


@router.get("/estado-resultado", response_model=EstadoResultadoOut, dependencies=[_guard_liq])
def estado_resultado(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> EstadoResultadoOut:
    vendido = db.scalar(select(EstadoVehiculo).where(EstadoVehiculo.code == "VENDIDO"))
    ventas = db.scalars(
        select(ActaRecepcion).where(
            ActaRecepcion.tenant_id == tenant_id,
            ActaRecepcion.estado_id == vendido.id,
        )
    ).all()
    if desde is not None:
        ventas = [a for a in ventas if a.fecha_venta and a.fecha_venta >= desde]
    if hasta is not None:
        ventas = [a for a in ventas if a.fecha_venta and a.fecha_venta <= hasta]

    monto_transado = sum(a.precio_venta_final or 0 for a in ventas)
    comision_empresa = sum(calcular_comision(a.precio_venta_final or 0, a.tipo_comision) for a in ventas)
    acta_ids = {a.id for a in ventas}
    comisiones_ej = db.scalars(
        select(ComisionEjecutivo).where(ComisionEjecutivo.tenant_id == tenant_id)
    ).all()
    comisiones_ejecutivos = sum(c.monto for c in comisiones_ej if c.acta_id in acta_ids)

    # Abonos: retenidos (ingreso por gestión) y comprometidos (no devengados).
    retenido = db.scalar(select(EstadoAbono).where(EstadoAbono.code == "RETENIDO"))
    no_deveng = db.scalar(select(EstadoAbono).where(EstadoAbono.code == "NO_DEVENGADO"))
    ret_actas = db.scalars(
        select(ActaRecepcion).where(
            ActaRecepcion.tenant_id == tenant_id,
            ActaRecepcion.estado_abono_id == retenido.id,
        )
    ).all()
    if desde is not None:
        ret_actas = [a for a in ret_actas if a.fecha_resolucion_abono and a.fecha_resolucion_abono >= desde]
    if hasta is not None:
        ret_actas = [a for a in ret_actas if a.fecha_resolucion_abono and a.fecha_resolucion_abono <= hasta]
    abonos_retenidos = sum(a.exclusividad_abono for a in ret_actas)
    abonos_comprometidos = sum(
        a.exclusividad_abono for a in db.scalars(
            select(ActaRecepcion).where(
                ActaRecepcion.tenant_id == tenant_id,
                ActaRecepcion.estado_abono_id == no_deveng.id,
                ActaRecepcion.cerrada.is_(False),
            )
        ).all()
    )

    return EstadoResultadoOut(
        desde=desde, hasta=hasta,
        ventas_cantidad=len(ventas), monto_transado=monto_transado,
        comision_empresa=comision_empresa, comisiones_ejecutivos=comisiones_ejecutivos,
        margen_corretaje=comision_empresa - comisiones_ejecutivos,
        abonos_retenidos=abonos_retenidos, abonos_comprometidos=abonos_comprometidos,
    )

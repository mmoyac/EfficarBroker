"""Endpoints del VEHÍCULO como entidad fuerte.

Ya no es el recurso operativo del Módulo 2 (eso vive en /actas). Aquí quedan:
consulta de fichas, historial de recepciones, lookups para el formulario, y la
mantención de la ficha física con permisos escalonados según su historial
documental.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user, get_effective_tenant_id, require_roles
from src.models.acta import ActaRecepcion
from src.models.catalogs import (
    Color,
    Combustible,
    EstadoVehiculo,
    TipoVehiculo,
    VehiculoVersion,
)
from src.models.cliente import Cliente
from src.models.tenant import Tenant
from src.models.user import User
from src.models.vehiculo import Vehiculo
from src.schemas.acta import (
    ActaHistorialItemOut,
    VehiculoFichaOut,
    VehiculoLookupOut,
)
from src.schemas.vehiculo import (
    ClienteLookupOut,
    ClienteOut,
    VehiculoGlobalLookupOut,
    VehiculoUpdateIn,
)
from src.services import audit_service

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])

_guard = Depends(require_roles("Sales", "Management", "TenantAdmin"))
_ROLES_TRANSVERSALES = ("Management", "TenantAdmin", "SuperAdmin")
FIRMADO = ("CONTRATO_ACEPTADO", "PUBLICADO", "VENDIDO")


def _cliente_out(c: Cliente) -> ClienteOut:
    return ClienteOut(
        id=c.id, rut=c.rut, nombre=c.nombre, email=c.email, telefono=c.telefono,
        domicilio=c.domicilio, comuna_id=c.comuna_id,
        comuna=c.comuna.nombre if c.comuna else None,
    )


def _ficha(v: Vehiculo) -> VehiculoFichaOut:
    return VehiculoFichaOut(
        id=v.id, ppu=v.ppu, version_id=v.version_id,
        marca=v.marca_nombre, modelo=v.modelo_nombre, version=v.version.nombre,
        anio=v.anio, n_motor=v.n_motor, n_chasis=v.n_chasis,
        color=v.color.nombre if v.color else None, color_id=v.color_id,
        tipo_vehiculo=v.tipo_vehiculo.nombre if v.tipo_vehiculo else None,
        combustible=v.combustible.nombre if v.combustible else None,
    )


def _scoped(db: Session, vehiculo_id: int, tenant_id: int) -> Vehiculo:
    v = db.get(Vehiculo, vehiculo_id)
    if v is None or v.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    return v


def _validate_catalog(db: Session, model, id_: int | None, msg: str) -> None:
    if id_ is not None and db.get(model, id_) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


# ---------------------------------------------------------------- lookups
# (rutas literales antes que /{vehiculo_id} para no colisionar)


@router.get("/lookup/cliente", response_model=ClienteLookupOut, dependencies=[_guard])
def buscar_cliente_por_rut(
    rut: str,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> ClienteLookupOut:
    rut_norm = rut.strip().upper()
    if not rut_norm:
        return ClienteLookupOut(found=False, cliente=None)
    cliente = db.scalar(
        select(Cliente).where(
            Cliente.tenant_id == tenant_id, func.upper(Cliente.rut) == rut_norm
        )
    )
    if cliente is None:
        return ClienteLookupOut(found=False, cliente=None)
    return ClienteLookupOut(found=True, cliente=_cliente_out(cliente))


@router.get("/lookup", response_model=VehiculoLookupOut, dependencies=[_guard])
def lookup_por_ppu(
    ppu: str,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> VehiculoLookupOut:
    """Ficha del vehículo en el tenant + si tiene acta activa, para precargar el formulario."""
    ppu_norm = ppu.strip().upper()
    if not ppu_norm:
        return VehiculoLookupOut(found=False)
    v = db.scalar(
        select(Vehiculo).where(Vehiculo.tenant_id == tenant_id, func.upper(Vehiculo.ppu) == ppu_norm)
    )
    if v is None:
        return VehiculoLookupOut(found=False)
    total = db.scalar(select(func.count(ActaRecepcion.id)).where(ActaRecepcion.vehiculo_id == v.id)) or 0
    activa = db.scalar(
        select(ActaRecepcion.id).where(
            ActaRecepcion.vehiculo_id == v.id, ActaRecepcion.cerrada.is_(False)
        )
    )
    return VehiculoLookupOut(
        found=True, vehiculo=_ficha(v),
        tiene_acta_activa=activa is not None, total_actas=int(total),
    )


@router.get("/lookup/vehiculo-global", response_model=VehiculoGlobalLookupOut, dependencies=[_guard])
def buscar_vehiculo_global_por_ppu(
    ppu: str,
    db: Session = Depends(get_db),
) -> VehiculoGlobalLookupOut:
    ppu_norm = ppu.strip().upper()
    if not ppu_norm:
        return VehiculoGlobalLookupOut(found=False, vehiculo=None)

    v = db.scalar(
        select(Vehiculo)
        .where(func.upper(Vehiculo.ppu) == ppu_norm)
        .order_by(Vehiculo.created_at.desc())
        .limit(1)
    )
    if v is None:
        return VehiculoGlobalLookupOut(found=False, vehiculo=None)

    tenant = db.get(Tenant, v.tenant_id)
    # El estado vive en el acta más reciente del vehículo.
    ultima = db.scalar(
        select(ActaRecepcion)
        .where(ActaRecepcion.vehiculo_id == v.id)
        .order_by(ActaRecepcion.fecha_recepcion.desc(), ActaRecepcion.id.desc())
        .limit(1)
    )
    estado_code = ultima.estado.code if ultima else "SIN_ACTA"
    return VehiculoGlobalLookupOut(
        found=True,
        vehiculo={
            "id": v.id,
            "tenant_id": tenant.id,
            "tenant_nombre": tenant.nombre,
            "ppu": v.ppu,
            "marca": v.marca_nombre,
            "modelo": v.modelo_nombre,
            "anio": v.anio,
            "n_motor": v.n_motor,
            "n_chasis": v.n_chasis,
            "estado_code": estado_code,
        },
    )


# ---------------------------------------------------------------- fichas


@router.get("", response_model=list[VehiculoFichaOut], dependencies=[_guard])
def listar_vehiculos(
    q: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> list[VehiculoFichaOut]:
    """Fichas del tenant, opcionalmente filtradas por PPU (mantenedor)."""
    stmt = select(Vehiculo).where(Vehiculo.tenant_id == tenant_id)
    if q:
        stmt = stmt.where(func.upper(Vehiculo.ppu).like(f"%{q.strip().upper()}%"))
    vehiculos = db.scalars(stmt.order_by(Vehiculo.ppu)).all()
    return [_ficha(v) for v in vehiculos]


@router.get("/{vehiculo_id}", response_model=VehiculoFichaOut, dependencies=[_guard])
def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> VehiculoFichaOut:
    return _ficha(_scoped(db, vehiculo_id, tenant_id))


@router.get("/{vehiculo_id}/actas", response_model=list[ActaHistorialItemOut], dependencies=[_guard])
def historial_de_actas(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> list[ActaHistorialItemOut]:
    """Historial de recepciones del vehículo, de la más reciente a la más antigua."""
    v = _scoped(db, vehiculo_id, tenant_id)
    actas = db.scalars(
        select(ActaRecepcion)
        .where(ActaRecepcion.vehiculo_id == v.id)
        .order_by(ActaRecepcion.fecha_recepcion.desc(), ActaRecepcion.id.desc())
    ).all()
    return [
        ActaHistorialItemOut(
            id=a.id, cliente=a.cliente.nombre, captador=a.captador.nombre,
            estado_code=a.estado.code, fecha_recepcion=a.fecha_recepcion,
            fecha_venta=a.fecha_venta, precio_venta_pactado=a.precio_venta_pactado,
            precio_venta_final=a.precio_venta_final, cerrada=a.cerrada,
            motivo_cierre=a.motivo_cierre.nombre if a.motivo_cierre else None,
        )
        for a in actas
    ]


# ---------------------------------------------------------------- mantención


@router.patch("/{vehiculo_id}", response_model=VehiculoFichaOut, dependencies=[_guard])
def editar_ficha(
    vehiculo_id: int,
    body: VehiculoUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> VehiculoFichaOut:
    v = _scoped(db, vehiculo_id, tenant_id)

    # ¿El auto tiene alguna acta firmada o cerrada? Si sí, corregir la ficha
    # afecta documentos ya emitidos: solo roles altos, con motivo y auditoría.
    tiene_historial = db.scalar(
        select(ActaRecepcion.id).where(
            ActaRecepcion.vehiculo_id == v.id,
            (ActaRecepcion.cerrada.is_(True)) | (ActaRecepcion.estado.has(EstadoVehiculo.code.in_(FIRMADO))),
        )
    ) is not None
    es_transversal = current.role.code in _ROLES_TRANSVERSALES

    if tiene_historial:
        if not es_transversal:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este auto tiene actas firmadas; solo Management puede corregir su ficha.",
            )
        if not body.motivo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe indicar un motivo: el cambio afecta documentos ya emitidos.",
            )
    else:
        # Sin historial: el captador de su acta activa puede corregir.
        acta_activa = db.scalar(
            select(ActaRecepcion).where(
                ActaRecepcion.vehiculo_id == v.id, ActaRecepcion.cerrada.is_(False)
            )
        )
        es_captador = acta_activa is not None and acta_activa.captador_user_id == current.id
        if not (es_transversal or es_captador):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el captador o un administrador puede editar esta ficha.",
            )

    patch = body.model_dump(exclude_unset=True)
    patch.pop("motivo", None)
    if not patch:
        return _ficha(v)

    # La PPU es la identidad del auto: solo roles altos pueden cambiarla.
    if patch.get("ppu") is not None:
        if not es_transversal:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo Management puede cambiar la PPU.",
            )
        ppu_norm = patch["ppu"].strip().upper()
        if not ppu_norm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PPU inválida")
        dup = db.scalar(
            select(Vehiculo.id).where(
                Vehiculo.tenant_id == tenant_id, func.upper(Vehiculo.ppu) == ppu_norm, Vehiculo.id != v.id
            )
        )
        if dup:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un vehículo con esa PPU en este tenant")
        v.ppu = ppu_norm

    if patch.get("version_id") is not None:
        _validate_catalog(db, VehiculoVersion, patch["version_id"], "Versión inválida")
        v.version_id = patch["version_id"]
    if patch.get("color_id") is not None:
        _validate_catalog(db, Color, patch["color_id"], "Color inválido")
        v.color_id = patch["color_id"]
    if patch.get("tipo_vehiculo_id") is not None:
        _validate_catalog(db, TipoVehiculo, patch["tipo_vehiculo_id"], "Tipo de vehículo inválido")
        v.tipo_vehiculo_id = patch["tipo_vehiculo_id"]
    if patch.get("combustible_id") is not None:
        _validate_catalog(db, Combustible, patch["combustible_id"], "Combustible inválido")
        v.combustible_id = patch["combustible_id"]
    for campo in ("anio", "n_motor", "n_chasis"):
        if campo in patch:
            setattr(v, campo, patch[campo])

    db.flush()
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=v.id,
        estado_anterior=None, estado_nuevo=None,
        payload={
            "accion": "editar_ficha_vehiculo",
            "campos": sorted(patch.keys()),
            "motivo": body.motivo,
            "con_historial": tiene_historial,
        },
    )
    db.refresh(v)
    return _ficha(v)


@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_guard])
def eliminar_vehiculo(
    vehiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> None:
    v = _scoped(db, vehiculo_id, tenant_id)
    tiene_actas = db.scalar(select(ActaRecepcion.id).where(ActaRecepcion.vehiculo_id == v.id)) is not None
    if tiene_actas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un vehículo con historial de actas.",
        )
    if current.role.code not in _ROLES_TRANSVERSALES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede eliminar una ficha de vehículo.",
        )
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=v.id,
        estado_anterior=None, estado_nuevo="ELIMINADO",
        payload={"accion": "eliminar_vehiculo", "ppu": v.ppu},
    )
    db.delete(v)
    db.commit()

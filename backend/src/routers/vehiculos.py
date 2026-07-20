from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user, get_effective_tenant_id, require_roles
from src.models.catalogs import (
    Combustible,
    Comuna,
    EstadoVehiculo,
    TipoComision,
    TipoVehiculo,
    VehiculoVersion,
)
from src.models.cliente import Cliente
from src.models.tenant import Tenant
from src.models.sucursal import Sucursal
from src.models.user import User
from src.models.vehiculo import (
    ChecklistItem,
    Vehiculo,
    VehiculoChecklist,
    VehiculoEstadoHistorial,
)
from src.models.catalogs import Role
from src.schemas.vehiculo import (
    ActaCreate,
    ClienteLookupOut,
    ClienteOut,
    RegistrarVentaIn,
    VehiculoUpdateIn,
    VehiculoChecklistOut,
    VehiculoDetailOut,
    VehiculoGlobalLookupOut,
    VehiculoOut,
)
from src.services import audit_service
from src.services.acta_pdf import build_acta_orden_pdf
from src.utils.comision import calcular_comision, calcular_liquidacion

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])

# El acta la levantan ejecutivos y gestión (SuperAdmin pasa por transversalidad).
_guard = Depends(require_roles("Sales", "Management", "TenantAdmin"))

RECEPCIONADO = "RECEPCIONADO"
CONTRATO_ACEPTADO = "CONTRATO_ACEPTADO"
PUBLICADO = "PUBLICADO"
VENDIDO = "VENDIDO"


def _estado(db: Session, code: str) -> EstadoVehiculo:
    estado = db.scalar(select(EstadoVehiculo).where(EstadoVehiculo.code == code))
    if estado is None:
        raise HTTPException(status_code=500, detail=f"Estado {code} no está en el catálogo")
    return estado


def _validate_catalog(db: Session, model, id_: int | None, msg: str) -> None:
    """Valida que un id de catálogo (opcional) exista; None se acepta."""
    if id_ is not None and db.get(model, id_) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _cliente_out(c: Cliente) -> ClienteOut:
    return ClienteOut(
        id=c.id, rut=c.rut, nombre=c.nombre, email=c.email, telefono=c.telefono,
        domicilio=c.domicilio, comuna_id=c.comuna_id,
        comuna=c.comuna.nombre if c.comuna else None,
    )


def _to_out(v: Vehiculo) -> VehiculoOut:
    comision = calcular_comision(v.precio_venta_pactado, v.tipo_comision)
    liquidacion = calcular_liquidacion(v.precio_venta_pactado, v.tipo_comision)
    return VehiculoOut(
        id=v.id,
        ppu=v.ppu,
        version_id=v.version_id,
        sucursal_id=v.sucursal_id,
        sucursal_venta_id=v.sucursal_venta_id,
        marca=v.marca,
        modelo=v.modelo,
        version=v.version.nombre if v.version else None,
        anio=v.anio,
        km_ingreso=v.km_ingreso,
        color=v.color,
        tipo_vehiculo=v.tipo_vehiculo.nombre if v.tipo_vehiculo else None,
        combustible=v.combustible.nombre if v.combustible else None,
        estado=v.estado.nombre, estado_code=v.estado.code,
        cliente=v.cliente.nombre, captador=v.captador.nombre,
        vendedor=v.vendedor.nombre if v.vendedor else None,
        sucursal=v.sucursal.nombre,
        sucursal_venta=v.sucursal_venta.nombre,
        derivado=v.sucursal_venta_id != v.sucursal_id,
        tipo_comision=v.tipo_comision.nombre if v.tipo_comision else None,
        precio_venta_pactado=v.precio_venta_pactado,
        comision=comision, liquidacion=liquidacion,
        precio_venta_final=v.precio_venta_final,
        fecha_recepcion=v.fecha_recepcion, fecha_venta=v.fecha_venta,
    )


def _to_detail(v: Vehiculo) -> VehiculoDetailOut:
    return VehiculoDetailOut(
        **_to_out(v).model_dump(),
        n_motor=v.n_motor, n_chasis=v.n_chasis,
        vigencia_dias=v.vigencia_dias, exclusividad_abono=v.exclusividad_abono,
        cliente_detalle=_cliente_out(v.cliente),
        checklist=[
            VehiculoChecklistOut(
                checklist_item_id=c.checklist_item_id, item=c.item.nombre, tipo=c.item.tipo,
                presente=c.presente, estado=c.estado,
                fecha_vencimiento=c.fecha_vencimiento, observacion=c.observacion,
            )
            for c in sorted(v.checklist, key=lambda c: c.item.orden)
        ],
    )


def _registrar_historial(db: Session, vehiculo: Vehiculo, user_id: int) -> None:
    """Registra el estado ACTUAL del vehículo en el historial (para KPIs temporales)."""
    db.add(VehiculoEstadoHistorial(
        tenant_id=vehiculo.tenant_id, vehiculo_id=vehiculo.id,
        estado_id=vehiculo.estado_id, user_id=user_id,
    ))


def _scoped(db: Session, vehiculo_id: int, tenant_id: int) -> Vehiculo:
    v = db.get(Vehiculo, vehiculo_id)
    if v is None or v.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    return v


@router.post("", response_model=VehiculoDetailOut, status_code=status.HTTP_201_CREATED, dependencies=[_guard])
def crear_acta(
    body: ActaCreate,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> VehiculoDetailOut:
    # PPU única por tenant
    if db.scalar(select(Vehiculo.id).where(Vehiculo.tenant_id == tenant_id, Vehiculo.ppu == body.ppu)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un vehículo con esa PPU en este tenant")

    # Sucursal de origen del tenant
    suc = db.get(Sucursal, body.sucursal_id)
    if suc is None or suc.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal inválida")

    # Sucursal de venta (= origen si es venta propia; distinta si se deriva)
    suc_venta = db.get(Sucursal, body.sucursal_venta_id)
    if suc_venta is None or suc_venta.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal de venta inválida")

    version = db.get(VehiculoVersion, body.version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Versión de vehículo inválida")

    # Catálogos del vehículo (tipo de comisión obligatorio; el resto opcional)
    tipo_comision = db.get(TipoComision, body.tipo_comision_id)
    if tipo_comision is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de comisión inválido")
    _validate_catalog(db, TipoVehiculo, body.tipo_vehiculo_id, "Tipo de vehículo inválido")
    _validate_catalog(db, Combustible, body.combustible_id, "Combustible inválido")
    _validate_catalog(db, Comuna, body.cliente.comuna_id, "Comuna inválida")

    # get-or-create cliente por RUT
    cliente = db.scalar(
        select(Cliente).where(Cliente.tenant_id == tenant_id, Cliente.rut == body.cliente.rut)
    )
    if cliente is None:
        cliente = Cliente(
            tenant_id=tenant_id, rut=body.cliente.rut, nombre=body.cliente.nombre,
            email=body.cliente.email, telefono=body.cliente.telefono,
            domicilio=body.cliente.domicilio, comuna_id=body.cliente.comuna_id,
        )
        db.add(cliente)
        db.flush()
    else:
        cliente.nombre = body.cliente.nombre
        cliente.email = body.cliente.email
        cliente.telefono = body.cliente.telefono
        cliente.domicilio = body.cliente.domicilio
        cliente.comuna_id = body.cliente.comuna_id

    estado_recep = _estado(db, RECEPCIONADO)
    modelo = version.modelo
    marca = modelo.marca
    vehiculo = Vehiculo(
        tenant_id=tenant_id,
        ppu=body.ppu,
        marca=marca.nombre,
        modelo=modelo.nombre,
        version_id=version.id,
        anio=body.anio,
        n_motor=body.n_motor, n_chasis=body.n_chasis, km_ingreso=body.km_ingreso,
        color=body.color, tipo_vehiculo_id=body.tipo_vehiculo_id, combustible_id=body.combustible_id,
        estado_id=estado_recep.id, cliente_id=cliente.id, captador_user_id=current.id,
        sucursal_id=suc.id, sucursal_venta_id=suc_venta.id,
        tipo_comision_id=tipo_comision.id,
        precio_venta_pactado=body.precio_venta_pactado,
        vigencia_dias=body.vigencia_dias, exclusividad_abono=body.exclusividad_abono,
        fecha_recepcion=date.today(),
    )
    db.add(vehiculo)
    db.flush()

    # Checklist: solo items válidos del catálogo
    valid_items = {i.id for i in db.scalars(select(ChecklistItem)).all()}
    for entry in body.checklist:
        if entry.checklist_item_id not in valid_items:
            continue
        db.add(VehiculoChecklist(
            vehiculo_id=vehiculo.id, checklist_item_id=entry.checklist_item_id,
            presente=entry.presente, estado=entry.estado,
            fecha_vencimiento=entry.fecha_vencimiento, observacion=entry.observacion,
        ))

    db.flush()
    _registrar_historial(db, vehiculo, current.id)
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=vehiculo.id,
        estado_anterior=None, estado_nuevo=RECEPCIONADO,
        payload={"ppu": vehiculo.ppu, "cliente_rut": cliente.rut},
    )  # audit_service hace commit
    db.refresh(vehiculo)
    return _to_detail(vehiculo)


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
            Cliente.tenant_id == tenant_id,
            func.upper(Cliente.rut) == rut_norm,
        )
    )
    if cliente is None:
        return ClienteLookupOut(found=False, cliente=None)
    return ClienteLookupOut(found=True, cliente=_cliente_out(cliente))


@router.get("/lookup/vehiculo-global", response_model=VehiculoGlobalLookupOut, dependencies=[_guard])
def buscar_vehiculo_global_por_ppu(
    ppu: str,
    db: Session = Depends(get_db),
) -> VehiculoGlobalLookupOut:
    ppu_norm = ppu.strip().upper()
    if not ppu_norm:
        return VehiculoGlobalLookupOut(found=False, vehiculo=None)

    row = db.execute(
        select(Vehiculo, Tenant, EstadoVehiculo)
        .join(Tenant, Tenant.id == Vehiculo.tenant_id)
        .join(EstadoVehiculo, EstadoVehiculo.id == Vehiculo.estado_id)
        .where(func.upper(Vehiculo.ppu) == ppu_norm)
        .order_by(Vehiculo.created_at.desc())
        .limit(1)
    ).first()

    if row is None:
        return VehiculoGlobalLookupOut(found=False, vehiculo=None)

    vehiculo, tenant, estado = row
    return VehiculoGlobalLookupOut(
        found=True,
        vehiculo={
            "id": vehiculo.id,
            "tenant_id": tenant.id,
            "tenant_nombre": tenant.nombre,
            "ppu": vehiculo.ppu,
            "marca": vehiculo.marca,
            "modelo": vehiculo.modelo,
            "anio": vehiculo.anio,
            "n_motor": vehiculo.n_motor,
            "n_chasis": vehiculo.n_chasis,
            "estado_code": estado.code,
        },
    )


_ROLES_TRANSVERSALES = ("Management", "TenantAdmin", "SuperAdmin")


@router.get("", response_model=list[VehiculoOut], dependencies=[_guard])
def listar_vehiculos(
    mine: bool = False,
    derivadas: bool = False,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> list[VehiculoOut]:
    stmt = select(Vehiculo).where(Vehiculo.tenant_id == tenant_id)
    if mine:
        stmt = stmt.where(Vehiculo.captador_user_id == current.id)
    if derivadas:
        # Solo autos derivados (venta en sucursal distinta a la de origen).
        stmt = stmt.where(Vehiculo.sucursal_venta_id != Vehiculo.sucursal_id)
        # Los ejecutivos ven solo las derivaciones hacia SU sucursal de venta;
        # los roles transversales ven todas las del tenant.
        if current.role.code not in _ROLES_TRANSVERSALES:
            stmt = stmt.where(Vehiculo.sucursal_venta_id == current.sucursal_id)
    vehiculos = db.scalars(stmt.order_by(Vehiculo.created_at.desc())).all()
    return [_to_out(v) for v in vehiculos]


@router.get("/{vehiculo_id}", response_model=VehiculoDetailOut, dependencies=[_guard])
def detalle_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> VehiculoDetailOut:
    return _to_detail(_scoped(db, vehiculo_id, tenant_id))


@router.get("/{vehiculo_id}/documento-firma", dependencies=[_guard])
def descargar_documento_firma(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
):
    v = _scoped(db, vehiculo_id, tenant_id)
    if v.estado.code not in (CONTRATO_ACEPTADO, PUBLICADO, VENDIDO):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Documento disponible desde CONTRATO_ACEPTADO (estado actual: {v.estado.code})",
        )

    can_view = (
        current.role.code in ("TenantAdmin", "Management", "SuperAdmin")
        or v.captador_user_id == current.id
        or v.vendedor_user_id == current.id
    )
    if not can_view:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para descargar este documento")

    tenant = db.get(Tenant, v.tenant_id)
    pdf = build_acta_orden_pdf(v, tenant)
    filename = f"acta-orden-{v.ppu}.pdf"
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{vehiculo_id}/aceptar-terminos", response_model=VehiculoDetailOut, dependencies=[_guard])
def aceptar_terminos(
    vehiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> VehiculoDetailOut:
    v = _scoped(db, vehiculo_id, tenant_id)
    if v.estado.code != RECEPCIONADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El vehículo no está en RECEPCIONADO (estado actual: {v.estado.code})",
        )
    estado_ant = v.estado.code
    v.estado_id = _estado(db, CONTRATO_ACEPTADO).id
    db.flush()
    _registrar_historial(db, v, current.id)
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=v.id,
        estado_anterior=estado_ant, estado_nuevo=CONTRATO_ACEPTADO,
        payload={"accion": "aceptar_terminos_manual"},
    )
    db.refresh(v)
    return _to_detail(v)


@router.patch("/{vehiculo_id}", response_model=VehiculoDetailOut, dependencies=[_guard])
def editar_vehiculo_recepcionado(
    vehiculo_id: int,
    body: VehiculoUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> VehiculoDetailOut:
    v = _scoped(db, vehiculo_id, tenant_id)
    if v.estado.code != RECEPCIONADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede editar en RECEPCIONADO (estado actual: {v.estado.code})",
        )

    can_edit = (
        current.role.code in ("TenantAdmin", "Management", "SuperAdmin")
        or v.captador_user_id == current.id
    )
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el captador o un administrador puede editar esta captación.",
        )

    patch = body.model_dump(exclude_unset=True)
    if not patch:
        return _to_detail(v)

    if "ppu" in patch and patch["ppu"] is not None:
        ppu_norm = patch["ppu"].strip().upper()
        if not ppu_norm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PPU inválida")
        exists = db.scalar(
            select(Vehiculo.id)
            .where(Vehiculo.tenant_id == tenant_id, Vehiculo.ppu == ppu_norm, Vehiculo.id != v.id)
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un vehículo con esa PPU en este tenant")
        v.ppu = ppu_norm

    if "version_id" in patch and patch["version_id"] is not None:
        version = db.get(VehiculoVersion, patch["version_id"])
        if version is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Versión de vehículo inválida")
        v.version_id = version.id
        v.marca = version.modelo.marca.nombre
        v.modelo = version.modelo.nombre

    if "sucursal_id" in patch and patch["sucursal_id"] is not None:
        suc = db.get(Sucursal, patch["sucursal_id"])
        if suc is None or suc.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal inválida")
        v.sucursal_id = suc.id

    if "sucursal_venta_id" in patch and patch["sucursal_venta_id"] is not None:
        suc_venta = db.get(Sucursal, patch["sucursal_venta_id"])
        if suc_venta is None or suc_venta.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal de venta inválida")
        v.sucursal_venta_id = suc_venta.id

    if "anio" in patch and patch["anio"] is not None:
        v.anio = patch["anio"]
    if "n_motor" in patch:
        v.n_motor = patch["n_motor"].strip() if patch["n_motor"] else None
    if "n_chasis" in patch:
        v.n_chasis = patch["n_chasis"].strip() if patch["n_chasis"] else None
    if "km_ingreso" in patch and patch["km_ingreso"] is not None:
        v.km_ingreso = patch["km_ingreso"]
    if "color" in patch:
        v.color = patch["color"].strip() if patch["color"] else None
    if "tipo_vehiculo_id" in patch:
        _validate_catalog(db, TipoVehiculo, patch["tipo_vehiculo_id"], "Tipo de vehículo inválido")
        v.tipo_vehiculo_id = patch["tipo_vehiculo_id"]
    if "combustible_id" in patch:
        _validate_catalog(db, Combustible, patch["combustible_id"], "Combustible inválido")
        v.combustible_id = patch["combustible_id"]
    if "tipo_comision_id" in patch and patch["tipo_comision_id"] is not None:
        _validate_catalog(db, TipoComision, patch["tipo_comision_id"], "Tipo de comisión inválido")
        v.tipo_comision_id = patch["tipo_comision_id"]
    if "precio_venta_pactado" in patch and patch["precio_venta_pactado"] is not None:
        v.precio_venta_pactado = patch["precio_venta_pactado"]
    if "vigencia_dias" in patch and patch["vigencia_dias"] is not None:
        v.vigencia_dias = patch["vigencia_dias"]
    if "exclusividad_abono" in patch and patch["exclusividad_abono"] is not None:
        v.exclusividad_abono = patch["exclusividad_abono"]

    if "cliente_nombre" in patch and patch["cliente_nombre"] is not None:
        v.cliente.nombre = patch["cliente_nombre"].strip()
    if "cliente_email" in patch:
        v.cliente.email = patch["cliente_email"]
    if "cliente_telefono" in patch:
        v.cliente.telefono = patch["cliente_telefono"].strip() if patch["cliente_telefono"] else None
    if "cliente_domicilio" in patch:
        v.cliente.domicilio = patch["cliente_domicilio"].strip() if patch["cliente_domicilio"] else None
    if "cliente_comuna_id" in patch:
        _validate_catalog(db, Comuna, patch["cliente_comuna_id"], "Comuna inválida")
        v.cliente.comuna_id = patch["cliente_comuna_id"]

    db.flush()
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=v.id,
        estado_anterior=v.estado.code, estado_nuevo=v.estado.code,
        payload={"accion": "editar_captacion", "campos": sorted(patch.keys())},
    )
    db.refresh(v)
    return _to_detail(v)


@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_guard])
def eliminar_vehiculo(
    vehiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> None:
    v = _scoped(db, vehiculo_id, tenant_id)
    if v.estado.code != RECEPCIONADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede eliminar en RECEPCIONADO (estado actual: {v.estado.code})",
        )

    can_delete = (
        current.role.code in ("TenantAdmin", "Management", "SuperAdmin")
        or v.captador_user_id == current.id
    )
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el captador o un administrador puede eliminar esta captación.",
        )

    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=v.id,
        estado_anterior=v.estado.code, estado_nuevo="ELIMINADO",
        payload={"accion": "eliminar_captacion", "ppu": v.ppu},
    )
    db.delete(v)
    db.commit()


@router.post("/{vehiculo_id}/registrar-venta", response_model=VehiculoDetailOut, dependencies=[_guard])
def registrar_venta(
    vehiculo_id: int,
    body: RegistrarVentaIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> VehiculoDetailOut:
    v = _scoped(db, vehiculo_id, tenant_id)
    # Versión simplificada: vendible desde CONTRATO_ACEPTADO o PUBLICADO.
    if v.estado.code not in (CONTRATO_ACEPTADO, PUBLICADO):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El vehículo no está en condición de venta (estado actual: {v.estado.code})",
        )
    # Vendedor: usuario Sales activo del mismo tenant.
    vendedor = db.get(User, body.vendedor_user_id)
    if (
        vendedor is None or not vendedor.activo or vendedor.tenant_id != tenant_id
        or vendedor.role.code != "Sales"
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendedor inválido (debe ser un ejecutivo de ventas activo del tenant)")
    # El vendedor debe pertenecer a la sucursal de venta del vehículo (derivación).
    if vendedor.sucursal_id != v.sucursal_venta_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor no pertenece a la sucursal de venta del vehículo",
        )

    estado_ant = v.estado.code
    v.vendedor_user_id = vendedor.id
    v.precio_venta_final = body.precio_venta_final
    v.fecha_venta = date.today()
    v.estado_id = _estado(db, VENDIDO).id
    db.flush()
    _registrar_historial(db, v, current.id)
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="vehiculo", entidad_id=v.id,
        estado_anterior=estado_ant, estado_nuevo=VENDIDO,
        payload={
            "vendedor_id": vendedor.id, "captador_id": v.captador_user_id,
            "precio_venta_final": body.precio_venta_final,
        },
    )
    db.refresh(v)
    return _to_detail(v)

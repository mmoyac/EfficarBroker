"""Endpoints del ACTA DE RECEPCIÓN.

El acta es el recurso operativo del Módulo 2: crear, listar, aceptar términos,
documento de firma, registrar venta y cerrar sin venta. `/vehiculos` queda solo
para consultar fichas e historial.
"""

from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user, get_effective_tenant_id, require_roles
from src.models.acta import ActaChecklist, ActaEstadoHistorial, ActaRecepcion
from src.models.catalogs import (
    Color,
    Combustible,
    Comuna,
    EstadoAbono,
    EstadoChecklist,
    EstadoPagoComision,
    EstadoVehiculo,
    MotivoCierreActa,
    TipoComision,
    TipoComisionEjecutivo,
    TipoVehiculo,
    VehiculoVersion,
)
from src.models.comision import ComisionEjecutivo, ParametrosComision
from src.services.comision_ejecutivo import calcular_reparto
from src.models.cliente import Cliente
from src.models.sucursal import Sucursal
from src.models.tenant import Tenant
from src.models.user import User
from src.models.vehiculo import ChecklistItem, Vehiculo
from src.schemas.acta import (
    ActaChecklistOut,
    ActaCreate,
    ActaDetailOut,
    ActaOut,
    ActaUpdateIn,
    CerrarSinVentaIn,
    RecepcionarIn,
    RegistrarVentaIn,
    VehiculoFichaOut,
)
from src.schemas.vehiculo import ClienteOut
from src.services import audit_service
from src.services.acta_pdf import build_acta_orden_pdf
from src.utils.comision import calcular_comision, calcular_comision_neta, calcular_liquidacion

router = APIRouter(prefix="/actas", tags=["actas"])

# El acta la levantan ejecutivos y gestión (SuperAdmin pasa por transversalidad).
_guard = Depends(require_roles("Sales", "Management", "TenantAdmin"))

# Flujo: CAPTADO (captación online) -> RECEPCIONADO (auto presente + contrato
# firmado) -> VENDIDO. Recepcionar implica la firma del contrato.
CAPTADO = "CAPTADO"
RECEPCIONADO = "RECEPCIONADO"
CONTRATO_ACEPTADO = "CONTRATO_ACEPTADO"  # legado; el flujo nuevo no lo usa
PUBLICADO = "PUBLICADO"
VENDIDO = "VENDIDO"
# Estados desde los que un acta es vendible / imprimible.
VENDIBLE = (RECEPCIONADO, CONTRATO_ACEPTADO, PUBLICADO)
EDITABLE = (CAPTADO, RECEPCIONADO)

NO_DEVENGADO = "NO_DEVENGADO"
APLICADO_COMISION = "APLICADO_COMISION"
RETENIDO = "RETENIDO"

_ROLES_TRANSVERSALES = ("Management", "TenantAdmin", "SuperAdmin")


# ---------------------------------------------------------------- helpers


def _estado(db: Session, code: str) -> EstadoVehiculo:
    estado = db.scalar(select(EstadoVehiculo).where(EstadoVehiculo.code == code))
    if estado is None:
        raise HTTPException(status_code=500, detail=f"Estado {code} no está en el catálogo")
    return estado


def _estado_abono(db: Session, code: str) -> EstadoAbono:
    ea = db.scalar(select(EstadoAbono).where(EstadoAbono.code == code))
    if ea is None:
        raise HTTPException(status_code=500, detail=f"Estado de abono {code} no está en el catálogo")
    return ea


def _validate_catalog(db: Session, model, id_: int | None, msg: str) -> None:
    """Valida que un id de catálogo (opcional) exista; None se acepta."""
    if id_ is not None and db.get(model, id_) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _validar_vendedor(
    db: Session, vendedor_user_id: int | None, tenant_id: int,
    sucursal_venta_id: int, *, requerido: bool,
) -> User | None:
    """Vendedor nominado: Sales activo del tenant que pertenece a la sucursal de venta."""
    if vendedor_user_id is None:
        if requerido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Al derivar debes indicar el vendedor de la sucursal de venta.",
            )
        return None
    vendedor = db.get(User, vendedor_user_id)
    if (
        vendedor is None
        or vendedor.tenant_id != tenant_id
        or not vendedor.activo
        or vendedor.role.code != "Sales"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor debe ser un ejecutivo de ventas activo del tenant",
        )
    if vendedor.sucursal_id != sucursal_venta_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor no pertenece a la sucursal de venta",
        )
    return vendedor


def _ficha(v: Vehiculo) -> VehiculoFichaOut:
    return VehiculoFichaOut(
        id=v.id, ppu=v.ppu, version_id=v.version_id,
        marca_id=v.marca.id, modelo_id=v.modelo.id,
        marca=v.marca_nombre, modelo=v.modelo_nombre, version=v.version.nombre,
        anio=v.anio, n_motor=v.n_motor, n_chasis=v.n_chasis,
        color=v.color.nombre if v.color else None, color_id=v.color_id,
        tipo_vehiculo=v.tipo_vehiculo.nombre if v.tipo_vehiculo else None,
        combustible=v.combustible.nombre if v.combustible else None,
    )


def _to_out(a: ActaRecepcion) -> ActaOut:
    return ActaOut(
        id=a.id,
        vehiculo_id=a.vehiculo_id,
        vehiculo=_ficha(a.vehiculo),
        ppu=a.vehiculo.ppu,
        cliente=a.cliente.nombre,
        captador=a.captador.nombre,
        captador_user_id=a.captador_user_id,
        vendedor=a.vendedor.nombre if a.vendedor else None,
        vendedor_user_id=a.vendedor_user_id,
        estado=a.estado.nombre, estado_code=a.estado.code,
        sucursal_id=a.sucursal_id, sucursal_venta_id=a.sucursal_venta_id,
        sucursal=a.sucursal.nombre, sucursal_venta=a.sucursal_venta.nombre,
        derivado=a.derivado,
        km_ingreso=a.km_ingreso,
        tipo_comision=a.tipo_comision.nombre if a.tipo_comision else None,
        precio_venta_pactado=a.precio_venta_pactado,
        comision=calcular_comision(a.precio_venta_pactado, a.tipo_comision),
        liquidacion=calcular_liquidacion(a.precio_venta_pactado, a.tipo_comision),
        exclusividad_abono=a.exclusividad_abono,
        estado_abono=a.estado_abono.nombre, estado_abono_code=a.estado_abono.code,
        precio_venta_final=a.precio_venta_final,
        fecha_recepcion=a.fecha_recepcion, fecha_venta=a.fecha_venta,
        observaciones=a.observaciones,
        cerrada=a.cerrada,
        motivo_cierre=a.motivo_cierre.nombre if a.motivo_cierre else None,
        fecha_cierre=a.fecha_cierre,
        video_youtube_url=a.video_youtube_url,
        foto_principal_url=next((f.url for f in a.fotos if f.es_principal), None),
        fotos_count=len(a.fotos),
        tiene_video=a.video_youtube_url is not None,
    )


def _to_detail(a: ActaRecepcion) -> ActaDetailOut:
    return ActaDetailOut(
        **_to_out(a).model_dump(),
        vigencia_dias=a.vigencia_dias,
        cliente_detalle=_cliente_out(a.cliente),
        comision_neta=calcular_comision_neta(
            a.precio_venta_pactado, a.tipo_comision, a.exclusividad_abono
        ),
        checklist=[
            ActaChecklistOut(
                checklist_item_id=c.checklist_item_id,
                item=c.item.nombre,
                tipo=c.item.tipo.nombre,
                presente=c.presente,
                estado_checklist_id=c.estado_checklist_id,
                estado=c.estado_checklist.nombre if c.estado_checklist else None,
                fecha_vencimiento=c.fecha_vencimiento,
                observacion=c.observacion,
            )
            for c in sorted(a.checklist, key=lambda c: c.item.orden)
        ],
    )


def _cliente_out(c: Cliente) -> ClienteOut:
    return ClienteOut(
        id=c.id, rut=c.rut, nombre=c.nombre, email=c.email, telefono=c.telefono,
        domicilio=c.domicilio, comuna_id=c.comuna_id,
        comuna=c.comuna.nombre if c.comuna else None,
    )


def _registrar_historial(db: Session, acta: ActaRecepcion, user_id: int) -> None:
    """Registra el estado ACTUAL del acta en el historial (para KPIs temporales)."""
    db.add(ActaEstadoHistorial(
        tenant_id=acta.tenant_id, acta_id=acta.id,
        estado_id=acta.estado_id, user_id=user_id,
    ))


def _generar_comisiones(db: Session, acta: ActaRecepcion) -> None:
    """Al vender, genera la comisión de captación (captador) y de venta (vendedor).

    Monto y porcentajes se congelan. En venta propia el mismo ejecutivo recibe
    ambas. Si falta el tipo de comisión no hay base de cálculo y no se genera nada.
    """
    if acta.tipo_comision is None or not acta.precio_venta_final:
        return
    params = db.scalar(
        select(ParametrosComision).where(ParametrosComision.tenant_id == acta.tenant_id)
    )
    if params is None:
        # Default seguro si el tenant no tiene parámetros (no debería ocurrir).
        params = ParametrosComision(tenant_id=acta.tenant_id, pool_pct=20, captacion_pct=40, venta_pct=60)
    reparto = calcular_reparto(acta.precio_venta_final, acta.tipo_comision, params)

    pendiente = db.scalar(select(EstadoPagoComision).where(EstadoPagoComision.code == "PENDIENTE"))
    tipo_capt = db.scalar(select(TipoComisionEjecutivo).where(TipoComisionEjecutivo.code == "CAPTACION"))
    tipo_venta = db.scalar(select(TipoComisionEjecutivo).where(TipoComisionEjecutivo.code == "VENTA"))

    db.add(ComisionEjecutivo(
        tenant_id=acta.tenant_id, acta_id=acta.id, beneficiario_user_id=acta.captador_user_id,
        tipo_id=tipo_capt.id, monto=reparto.monto_captacion, estado_pago_id=pendiente.id,
        pool_pct=reparto.pool_pct, porcentaje_aplicado=reparto.captacion_pct,
    ))
    db.add(ComisionEjecutivo(
        tenant_id=acta.tenant_id, acta_id=acta.id, beneficiario_user_id=acta.vendedor_user_id,
        tipo_id=tipo_venta.id, monto=reparto.monto_venta, estado_pago_id=pendiente.id,
        pool_pct=reparto.pool_pct, porcentaje_aplicado=reparto.venta_pct,
    ))


def _scoped(db: Session, acta_id: int, tenant_id: int) -> ActaRecepcion:
    a = db.get(ActaRecepcion, acta_id)
    if a is None or a.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acta no encontrada")
    return a


# ---------------------------------------------------------------- crear


@router.post("", response_model=ActaDetailOut, status_code=status.HTTP_201_CREATED, dependencies=[_guard])
def crear_acta(
    body: ActaCreate,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ActaDetailOut:
    ppu = body.ppu.strip().upper()

    # Sucursal de recepción: por defecto la del usuario autenticado; solo se
    # exige elegirla si el usuario no tiene una (roles transversales).
    sucursal_id = body.sucursal_id if body.sucursal_id is not None else current.sucursal_id
    if sucursal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes indicar la sucursal de recepción (tu usuario no tiene una asignada).",
        )
    suc = db.get(Sucursal, sucursal_id)
    if suc is None or suc.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal inválida")

    suc_venta = db.get(Sucursal, body.sucursal_venta_id)
    if suc_venta is None or suc_venta.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal de venta inválida")

    version = db.get(VehiculoVersion, body.version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Versión de vehículo inválida")

    tipo_comision = db.get(TipoComision, body.tipo_comision_id)
    if tipo_comision is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de comisión inválido")
    _validate_catalog(db, TipoVehiculo, body.tipo_vehiculo_id, "Tipo de vehículo inválido")
    _validate_catalog(db, Combustible, body.combustible_id, "Combustible inválido")
    _validate_catalog(db, Color, body.color_id, "Color inválido")
    _validate_catalog(db, Comuna, body.cliente.comuna_id, "Comuna inválida")

    # Vendedor nominado. Al derivar (sucursal de venta != origen) es obligatorio
    # y debe pertenecer a la sucursal de venta. En venta propia es opcional.
    derivado = suc_venta.id != suc.id
    vendedor = _validar_vendedor(db, body.vendedor_user_id, tenant_id, suc_venta.id, requerido=derivado)

    # Validar el checklist antes de tocar la BD (400 no es conflicto de concurrencia).
    valid_items = {i.id for i in db.scalars(select(ChecklistItem)).all()}
    valid_estados = {e.id for e in db.scalars(select(EstadoChecklist)).all()}
    for entry in body.checklist:
        if entry.estado_checklist_id is not None and entry.estado_checklist_id not in valid_estados:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de checklist inválido",
            )

    # get-or-create de cliente y vehículo + creación del acta. Cualquier colisión
    # de unicidad (RUT, PPU o el índice de acta activa) bajo concurrencia real se
    # traduce a 409: un solo request gana con 201, el resto reintenta.
    try:
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
        else:
            cliente.nombre = body.cliente.nombre
            cliente.email = body.cliente.email
            cliente.telefono = body.cliente.telefono
            cliente.domicilio = body.cliente.domicilio
            cliente.comuna_id = body.cliente.comuna_id
        db.flush()

        vehiculo = db.scalar(
            select(Vehiculo).where(Vehiculo.tenant_id == tenant_id, func.upper(Vehiculo.ppu) == ppu)
        )
        if vehiculo is None:
            vehiculo = Vehiculo(
                tenant_id=tenant_id, ppu=ppu, version_id=version.id, anio=body.anio,
                n_motor=body.n_motor, n_chasis=body.n_chasis, color_id=body.color_id,
                tipo_vehiculo_id=body.tipo_vehiculo_id, combustible_id=body.combustible_id,
            )
            db.add(vehiculo)
            db.flush()
        else:
            # Ficha preexistente: rechazar si tiene acta vigente; refrescar datos físicos.
            activa = db.scalar(
                select(ActaRecepcion.id).where(
                    ActaRecepcion.vehiculo_id == vehiculo.id,
                    ActaRecepcion.cerrada.is_(False),
                )
            )
            if activa:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este vehículo ya tiene un acta vigente en el tenant",
                )
            vehiculo.version_id = version.id
            vehiculo.anio = body.anio
            if body.n_motor:
                vehiculo.n_motor = body.n_motor
            if body.n_chasis:
                vehiculo.n_chasis = body.n_chasis
            if body.color_id:
                vehiculo.color_id = body.color_id

        estado_recep = _estado(db, CAPTADO)
        acta = ActaRecepcion(
            tenant_id=tenant_id,
            vehiculo_id=vehiculo.id,
            cliente_id=cliente.id,
            captador_user_id=current.id,
            sucursal_id=suc.id,
            sucursal_venta_id=suc_venta.id,
            estado_id=estado_recep.id,
            km_ingreso=body.km_ingreso,
            fecha_recepcion=date.today(),
            precio_venta_pactado=body.precio_venta_pactado,
            vigencia_dias=body.vigencia_dias,
            tipo_comision_id=tipo_comision.id,
            exclusividad_abono=body.exclusividad_abono,
            estado_abono_id=_estado_abono(db, NO_DEVENGADO).id,
            fecha_cobro_abono=date.today() if body.exclusividad_abono > 0 else None,
            observaciones=body.observaciones,
            vendedor_user_id=vendedor.id if vendedor else None,
            cerrada=False,
        )
        db.add(acta)
        for entry in body.checklist:
            if entry.checklist_item_id not in valid_items:
                continue
            db.add(ActaChecklist(
                acta=acta, checklist_item_id=entry.checklist_item_id,
                presente=entry.presente, estado_checklist_id=entry.estado_checklist_id,
                fecha_vencimiento=entry.fecha_vencimiento, observacion=entry.observacion,
            ))
        db.flush()
    except IntegrityError:
        # Ventana de concurrencia: RUT, PPU o índice de acta activa colisionaron.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de creación concurrente para esta patente. Reintenta.",
        )

    _registrar_historial(db, acta, current.id)
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta", entidad_id=acta.id,
        estado_anterior=None, estado_nuevo=CAPTADO,
        payload={"ppu": vehiculo.ppu, "cliente_rut": cliente.rut, "vehiculo_id": vehiculo.id},
    )  # audit_service hace commit
    db.refresh(acta)
    return _to_detail(acta)


# ---------------------------------------------------------------- listar


@router.get("", response_model=list[ActaOut], dependencies=[_guard])
def listar_actas(
    mine: bool = False,
    derivadas: bool = False,
    incluir_cerradas: bool = True,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> list[ActaOut]:
    stmt = select(ActaRecepcion).where(ActaRecepcion.tenant_id == tenant_id)
    if mine:
        stmt = stmt.where(ActaRecepcion.captador_user_id == current.id)
    if derivadas:
        # Solo actas derivadas y aún gestionables.
        stmt = stmt.where(
            ActaRecepcion.sucursal_venta_id != ActaRecepcion.sucursal_id,
            ActaRecepcion.cerrada.is_(False),
        )
        # Los ejecutivos ven solo las derivaciones hacia SU sucursal de venta;
        # los roles transversales ven todas las del tenant.
        if current.role.code not in _ROLES_TRANSVERSALES:
            stmt = stmt.where(ActaRecepcion.sucursal_venta_id == current.sucursal_id)
    if not incluir_cerradas:
        stmt = stmt.where(ActaRecepcion.cerrada.is_(False))

    actas = db.scalars(
        stmt.order_by(ActaRecepcion.fecha_recepcion.desc(), ActaRecepcion.id.desc())
    ).all()
    return [_to_out(a) for a in actas]


@router.get("/{acta_id}", response_model=ActaDetailOut, dependencies=[_guard])
def obtener_acta(
    acta_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> ActaDetailOut:
    return _to_detail(_scoped(db, acta_id, tenant_id))


# ---------------------------------------------------------------- transiciones


@router.post("/{acta_id}/recepcionar", response_model=ActaDetailOut, dependencies=[_guard])
def recepcionar(
    acta_id: int,
    body: RecepcionarIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ActaDetailOut:
    """CAPTADO -> RECEPCIONADO: el auto llega a la sucursal.

    Recién aquí se registran los datos físicos (N° motor/chasis, km, color) y el
    checklist de 12 puntos, y se da por firmado el contrato (el documento de
    firma queda disponible desde este punto).
    """
    a = _scoped(db, acta_id, tenant_id)
    if a.estado.code != CAPTADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se recepciona un acta CAPTADA (estado actual: {a.estado.code})",
        )

    _validate_catalog(db, Color, body.color_id, "Color inválido")

    # Datos físicos del auto (inspección al recepcionar).
    v = a.vehiculo
    if body.n_motor is not None:
        v.n_motor = body.n_motor
    if body.n_chasis is not None:
        v.n_chasis = body.n_chasis
    if body.color_id is not None:
        v.color_id = body.color_id
    if body.km_ingreso is not None:
        a.km_ingreso = body.km_ingreso

    # Checklist de recepción (upsert por ítem).
    if body.checklist is not None:
        valid_items = {i.id for i in db.scalars(select(ChecklistItem)).all()}
        valid_estados = {e.id for e in db.scalars(select(EstadoChecklist)).all()}
        existentes = {c.checklist_item_id: c for c in a.checklist}
        for entry in body.checklist:
            if entry.checklist_item_id not in valid_items:
                continue
            if entry.estado_checklist_id is not None and entry.estado_checklist_id not in valid_estados:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de checklist inválido")
            row = existentes.get(entry.checklist_item_id)
            if row is None:
                db.add(ActaChecklist(
                    acta=a, checklist_item_id=entry.checklist_item_id,
                    presente=entry.presente, estado_checklist_id=entry.estado_checklist_id,
                    fecha_vencimiento=entry.fecha_vencimiento, observacion=entry.observacion,
                ))
            else:
                row.presente = entry.presente
                row.estado_checklist_id = entry.estado_checklist_id
                row.fecha_vencimiento = entry.fecha_vencimiento
                row.observacion = entry.observacion

    estado_ant = a.estado.code
    a.estado_id = _estado(db, RECEPCIONADO).id
    db.flush()
    _registrar_historial(db, a, current.id)
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta", entidad_id=a.id,
        estado_anterior=estado_ant, estado_nuevo=RECEPCIONADO,
        payload={"accion": "recepcionar", "ppu": v.ppu},
    )
    db.refresh(a)
    return _to_detail(a)


@router.post("/{acta_id}/registrar-venta", response_model=ActaDetailOut, dependencies=[_guard])
def registrar_venta(
    acta_id: int,
    body: RegistrarVentaIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ActaDetailOut:
    a = _scoped(db, acta_id, tenant_id)
    if a.cerrada:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El acta ya está cerrada")
    if a.estado.code not in VENDIBLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El acta no está en condición de venta (estado actual: {a.estado.code}). Debe estar recepcionada.",
        )

    vendedor = db.get(User, body.vendedor_user_id)
    if (
        vendedor is None
        or vendedor.tenant_id != tenant_id
        or not vendedor.activo
        or vendedor.role.code != "Sales"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor debe ser un ejecutivo de ventas activo del tenant",
        )
    # El vendedor debe pertenecer a la sucursal donde se gestiona la venta.
    if vendedor.sucursal_id != a.sucursal_venta_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor no pertenece a la sucursal de venta de esta acta",
        )

    estado_ant = a.estado.code
    a.vendedor_user_id = vendedor.id
    a.precio_venta_final = body.precio_venta_final
    a.fecha_venta = date.today()
    a.estado_id = _estado(db, VENDIDO).id
    # Cerrar el acta libera el vehículo para un futuro reingreso.
    a.cerrada = True
    a.fecha_cierre = date.today()
    # El abono se aplica a la comisión (no se devuelve en efectivo).
    if a.estado_abono.code == NO_DEVENGADO:
        a.estado_abono_id = _estado_abono(db, APLICADO_COMISION).id
        a.fecha_resolucion_abono = date.today()

    db.flush()
    # Generar las comisiones del ejecutivo (captación al captador, venta al vendedor).
    _generar_comisiones(db, a)
    _registrar_historial(db, a, current.id)
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta", entidad_id=a.id,
        estado_anterior=estado_ant, estado_nuevo=VENDIDO,
        payload={
            "accion": "registrar_venta",
            "vendedor_user_id": vendedor.id,
            "precio_venta_final": body.precio_venta_final,
            "abono": a.exclusividad_abono,
            "comision_neta": calcular_comision_neta(
                a.precio_venta_pactado, a.tipo_comision, a.exclusividad_abono
            ),
        },
    )
    db.refresh(a)
    return _to_detail(a)


@router.post("/{acta_id}/cerrar-sin-venta", response_model=ActaDetailOut, dependencies=[_guard])
def cerrar_sin_venta(
    acta_id: int,
    body: CerrarSinVentaIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ActaDetailOut:
    a = _scoped(db, acta_id, tenant_id)
    if a.cerrada:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El acta ya está cerrada")

    motivo = db.get(MotivoCierreActa, body.motivo_cierre_id)
    if motivo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Motivo de cierre inválido")

    estado_ant = a.estado.code
    a.cerrada = True
    a.motivo_cierre_id = motivo.id
    a.fecha_cierre = date.today()
    # Sin venta gestionada, el abono queda para la empresa como ingreso por
    # gestión (cubre fotografía, publicidad); no se devuelve.
    if a.estado_abono.code == NO_DEVENGADO:
        a.estado_abono_id = _estado_abono(db, RETENIDO).id
        a.fecha_resolucion_abono = date.today()

    db.flush()
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta", entidad_id=a.id,
        estado_anterior=estado_ant, estado_nuevo="CERRADA_SIN_VENTA",
        payload={
            "accion": "cerrar_sin_venta",
            "motivo": motivo.code,
            "observacion": body.observacion,
            "abono_retenido": a.exclusividad_abono,
        },
    )
    db.refresh(a)
    return _to_detail(a)


# ---------------------------------------------------------------- edición


@router.patch("/{acta_id}", response_model=ActaDetailOut, dependencies=[_guard])
def editar_acta(
    acta_id: int,
    body: ActaUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> ActaDetailOut:
    a = _scoped(db, acta_id, tenant_id)
    if a.estado.code not in EDITABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede editar mientras el acta no esté vendida (estado actual: {a.estado.code})",
        )
    # Puede editar: un rol transversal, el captador, o —si la venta se derivó a
    # otra sucursal— el equipo de esa sucursal de venta, que es quien gestiona el
    # auto derivado (lo recepciona, ajusta checklist y vende).
    es_equipo_venta_derivada = a.derivado and current.sucursal_id == a.sucursal_venta_id
    can_edit = (
        current.role.code in _ROLES_TRANSVERSALES
        or a.captador_user_id == current.id
        or es_equipo_venta_derivada
    )
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el captador, la sucursal de venta o un administrador puede editar esta acta.",
        )

    patch = body.model_dump(exclude_unset=True)
    if not patch:
        return _to_detail(a)

    for campo in ("sucursal_id", "sucursal_venta_id"):
        if patch.get(campo) is not None:
            suc = db.get(Sucursal, patch[campo])
            if suc is None or suc.tenant_id != tenant_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal inválida")
            setattr(a, campo, suc.id)

    if patch.get("tipo_comision_id") is not None:
        _validate_catalog(db, TipoComision, patch["tipo_comision_id"], "Tipo de comisión inválido")
        a.tipo_comision_id = patch["tipo_comision_id"]

    for campo in ("km_ingreso", "precio_venta_pactado", "vigencia_dias", "exclusividad_abono", "observaciones"):
        if campo in patch:
            setattr(a, campo, patch[campo])

    # Vendedor nominado: revalidar contra la sucursal de venta (ya actualizada).
    if "vendedor_user_id" in patch:
        derivado = a.sucursal_venta_id != a.sucursal_id
        vendedor = _validar_vendedor(
            db, patch["vendedor_user_id"], tenant_id, a.sucursal_venta_id, requerido=derivado
        )
        a.vendedor_user_id = vendedor.id if vendedor else None

    cliente_map = {
        "cliente_nombre": "nombre", "cliente_email": "email", "cliente_telefono": "telefono",
        "cliente_domicilio": "domicilio", "cliente_comuna_id": "comuna_id",
    }
    for k, attr in cliente_map.items():
        if k in patch:
            if k == "cliente_comuna_id":
                _validate_catalog(db, Comuna, patch[k], "Comuna inválida")
            setattr(a.cliente, attr, patch[k])

    # Checklist: si viene, se hace upsert por checklist_item_id (el cliente puede
    # haber entregado más o menos cosas de las registradas al inicio).
    if body.checklist is not None:
        valid_items = {i.id for i in db.scalars(select(ChecklistItem)).all()}
        valid_estados = {e.id for e in db.scalars(select(EstadoChecklist)).all()}
        existentes = {c.checklist_item_id: c for c in a.checklist}
        for entry in body.checklist:
            if entry.checklist_item_id not in valid_items:
                continue
            if entry.estado_checklist_id is not None and entry.estado_checklist_id not in valid_estados:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de checklist inválido"
                )
            row = existentes.get(entry.checklist_item_id)
            if row is None:
                db.add(ActaChecklist(
                    acta=a, checklist_item_id=entry.checklist_item_id,
                    presente=entry.presente, estado_checklist_id=entry.estado_checklist_id,
                    fecha_vencimiento=entry.fecha_vencimiento, observacion=entry.observacion,
                ))
            else:
                row.presente = entry.presente
                row.estado_checklist_id = entry.estado_checklist_id
                row.fecha_vencimiento = entry.fecha_vencimiento
                row.observacion = entry.observacion

    db.flush()
    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta", entidad_id=a.id,
        estado_anterior=a.estado.code, estado_nuevo=a.estado.code,
        payload={"accion": "editar_acta", "campos": sorted(patch.keys())},
    )
    db.refresh(a)
    return _to_detail(a)


@router.delete("/{acta_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_guard])
def eliminar_acta(
    acta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> None:
    a = _scoped(db, acta_id, tenant_id)
    if a.estado.code not in EDITABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede eliminar mientras el acta no esté vendida (estado actual: {a.estado.code})",
        )
    can_delete = (
        current.role.code in _ROLES_TRANSVERSALES
        or a.captador_user_id == current.id
    )
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el captador o un administrador puede eliminar esta acta.",
        )

    audit_service.log(
        db, tenant_id=tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta", entidad_id=a.id,
        estado_anterior=a.estado.code, estado_nuevo="ELIMINADA",
        payload={"accion": "eliminar_acta", "ppu": a.vehiculo.ppu},
    )
    db.delete(a)
    db.commit()


# ---------------------------------------------------------------- documento


@router.get("/{acta_id}/documento-firma", dependencies=[_guard])
def documento_firma(
    acta_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> StreamingResponse:
    a = _scoped(db, acta_id, tenant_id)
    if a.estado.code == CAPTADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El documento de firma está disponible desde la recepción del auto.",
        )

    can_view = (
        current.role.code in _ROLES_TRANSVERSALES
        or a.captador_user_id == current.id
        or a.vendedor_user_id == current.id
    )
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para descargar este documento",
        )

    tenant = db.get(Tenant, a.tenant_id)
    # El PDF se arma desde ESTA acta: refleja el cliente, el checklist y la
    # orden de venta de esta recepción, no los de otra del mismo vehículo.
    pdf = build_acta_orden_pdf(a, tenant)
    filename = f"acta-orden-{a.vehiculo.ppu}-{a.id}.pdf"
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

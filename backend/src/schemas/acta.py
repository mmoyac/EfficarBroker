"""Schemas del ACTA DE RECEPCIÓN.

El acta es la unión cliente <-> vehículo. Los datos de la ficha del auto se
exponen anidados en `vehiculo`; lo circunstancial (dueño, estado, orden de
venta, abono, venta, cierre) vive en el acta misma.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.vehiculo import ClienteIn, ClienteOut


class ChecklistEntryIn(BaseModel):
    # Sin strict: permite coerción de fecha ISO (string -> date) enviada por el frontend.
    checklist_item_id: int
    presente: bool = False
    estado_checklist_id: int | None = None
    fecha_vencimiento: date | None = None
    observacion: str | None = Field(default=None, max_length=255)


class ActaCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    cliente: ClienteIn
    # --- Ficha del vehículo (get-or-create por PPU) ---
    ppu: str = Field(min_length=4, max_length=10)
    version_id: int
    anio: int = Field(ge=1900, le=2100)
    n_motor: str | None = Field(default=None, max_length=60)
    n_chasis: str | None = Field(default=None, max_length=60)
    color_id: int | None = None
    tipo_vehiculo_id: int | None = None
    combustible_id: int | None = None
    # --- Del acta ---
    km_ingreso: int = Field(default=0, ge=0)
    sucursal_id: int  # sucursal de origen/captación
    sucursal_venta_id: int  # sucursal de venta (= sucursal_id si es venta propia)
    tipo_comision_id: int
    precio_venta_pactado: int = Field(default=0, ge=0)
    vigencia_dias: int = Field(default=30, ge=1)
    exclusividad_abono: int = Field(default=40000, ge=0)
    checklist: list[ChecklistEntryIn] = Field(default_factory=list)


class VehiculoFichaOut(BaseModel):
    """Identidad física del auto. Sin dueño, estado ni datos de venta."""

    id: int
    ppu: str
    version_id: int
    marca: str
    modelo: str
    version: str
    anio: int
    n_motor: str | None = None
    n_chasis: str | None = None
    color: str | None = None
    color_id: int | None = None
    tipo_vehiculo: str | None = None
    combustible: str | None = None


class ActaOut(BaseModel):
    id: int
    vehiculo_id: int
    vehiculo: VehiculoFichaOut
    ppu: str  # duplicado a nivel raíz para simplificar la grilla
    cliente: str
    captador: str
    vendedor: str | None = None
    estado: str
    estado_code: str
    sucursal_id: int
    sucursal_venta_id: int
    sucursal: str
    sucursal_venta: str
    derivado: bool
    km_ingreso: int
    tipo_comision: str | None = None
    precio_venta_pactado: int
    comision: int
    liquidacion: int
    exclusividad_abono: int
    estado_abono: str
    estado_abono_code: str
    precio_venta_final: int | None = None
    fecha_recepcion: date
    fecha_venta: date | None = None
    cerrada: bool
    motivo_cierre: str | None = None
    fecha_cierre: date | None = None


class ActaChecklistOut(BaseModel):
    checklist_item_id: int
    item: str
    tipo: str
    presente: bool
    estado_checklist_id: int | None = None
    estado: str | None = None
    fecha_vencimiento: date | None = None
    observacion: str | None = None


class ActaDetailOut(ActaOut):
    vigencia_dias: int
    cliente_detalle: ClienteOut
    checklist: list[ActaChecklistOut]
    # Saldo de comisión a cobrar al cierre, ya descontado el abono.
    comision_neta: int


class ActaUpdateIn(BaseModel):
    """Edición de los datos del acta mientras está en RECEPCIONADO."""

    model_config = ConfigDict(strict=True)

    sucursal_id: int | None = None
    sucursal_venta_id: int | None = None
    km_ingreso: int | None = Field(default=None, ge=0)
    tipo_comision_id: int | None = None
    precio_venta_pactado: int | None = Field(default=None, ge=0)
    vigencia_dias: int | None = Field(default=None, ge=1)
    exclusividad_abono: int | None = Field(default=None, ge=0)
    cliente_nombre: str | None = Field(default=None, min_length=1, max_length=150)
    cliente_email: EmailStr | None = None
    cliente_telefono: str | None = Field(default=None, max_length=30)
    cliente_domicilio: str | None = Field(default=None, max_length=255)
    cliente_comuna_id: int | None = None


class RegistrarVentaIn(BaseModel):
    model_config = ConfigDict(strict=True)

    vendedor_user_id: int
    precio_venta_final: int = Field(ge=0)


class CerrarSinVentaIn(BaseModel):
    model_config = ConfigDict(strict=True)

    motivo_cierre_id: int
    observacion: str | None = Field(default=None, max_length=255)


class ActaHistorialItemOut(BaseModel):
    """Un acta en el historial de recepciones de un vehículo."""

    id: int
    cliente: str
    captador: str
    estado_code: str
    fecha_recepcion: date
    fecha_venta: date | None = None
    precio_venta_pactado: int
    precio_venta_final: int | None = None
    cerrada: bool
    motivo_cierre: str | None = None


class VehiculoLookupOut(BaseModel):
    """Lookup por PPU dentro del tenant, para precargar el formulario."""

    found: bool
    vehiculo: VehiculoFichaOut | None = None
    tiene_acta_activa: bool = False
    total_actas: int = 0


class AbonoResumenItemOut(BaseModel):
    estado_code: str
    estado: str
    total: int
    cantidad: int


class AbonoResumenOut(BaseModel):
    # Cobrado pero aún no devengado: puede terminar aplicado o retenido.
    comprometido: int
    # Ya reconocido como ingreso (aplicado a comisión + retenido por gestión).
    ganado: int
    detalle: list[AbonoResumenItemOut]

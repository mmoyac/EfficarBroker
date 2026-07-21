from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nombre: str
    tipo_id: int
    requiere_vencimiento: bool
    orden: int


class ClienteIn(BaseModel):
    model_config = ConfigDict(strict=True)

    rut: str = Field(min_length=3, max_length=20)
    nombre: str = Field(min_length=1, max_length=150)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)
    domicilio: str | None = Field(default=None, max_length=255)
    comuna_id: int | None = None


class ChecklistEntryIn(BaseModel):
    # Sin strict: permite coerción de fecha ISO (string -> date) enviada por el frontend.
    checklist_item_id: int
    presente: bool = False
    estado: str | None = Field(default=None, max_length=40)
    fecha_vencimiento: date | None = None
    observacion: str | None = Field(default=None, max_length=255)


class ActaCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    cliente: ClienteIn
    # Vehículo
    ppu: str = Field(min_length=4, max_length=10)
    version_id: int
    anio: int = Field(ge=1900, le=2100)
    n_motor: str | None = Field(default=None, max_length=60)
    n_chasis: str | None = Field(default=None, max_length=60)
    km_ingreso: int = Field(default=0, ge=0)
    color: str | None = Field(default=None, max_length=40)
    tipo_vehiculo_id: int | None = None
    combustible_id: int | None = None
    sucursal_id: int  # sucursal de origen/captación
    sucursal_venta_id: int  # sucursal de venta (= sucursal_id si es venta propia)
    # Orden de venta
    tipo_comision_id: int
    precio_venta_pactado: int = Field(default=0, ge=0)
    vigencia_dias: int = Field(default=30, ge=1)
    exclusividad_abono: int = Field(default=40000, ge=0)
    # Checklist de 12 puntos
    checklist: list[ChecklistEntryIn] = Field(default_factory=list)


class VehiculoUpdateIn(BaseModel):
    """Corrección de la ficha física del auto (mantenedor).

    Los datos circunstanciales (dueño, orden de venta, sucursales) NO se editan
    aquí: pertenecen al acta. `motivo` es obligatorio cuando el auto ya tiene
    actas firmadas, porque el cambio afecta documentos ya emitidos.
    """

    model_config = ConfigDict(strict=True)

    ppu: str | None = Field(default=None, min_length=4, max_length=10)
    version_id: int | None = None
    anio: int | None = Field(default=None, ge=1900, le=2100)
    n_motor: str | None = Field(default=None, max_length=60)
    n_chasis: str | None = Field(default=None, max_length=60)
    color_id: int | None = None
    tipo_vehiculo_id: int | None = None
    combustible_id: int | None = None
    motivo: str | None = Field(default=None, max_length=255)


class ClienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rut: str
    nombre: str
    email: str | None = None
    telefono: str | None = None
    domicilio: str | None = None
    comuna_id: int | None = None
    comuna: str | None = None


class ClienteLookupOut(BaseModel):
    found: bool
    cliente: ClienteOut | None = None


class VehiculoOut(BaseModel):
    id: int
    ppu: str
    version_id: int | None = None
    sucursal_id: int
    sucursal_venta_id: int
    marca: str
    modelo: str
    version: str | None = None
    anio: int
    km_ingreso: int
    color: str | None = None
    tipo_vehiculo: str | None = None
    combustible: str | None = None
    estado: str
    estado_code: str
    cliente: str
    captador: str
    vendedor: str | None = None
    sucursal: str
    sucursal_venta: str
    derivado: bool
    tipo_comision: str | None = None
    precio_venta_pactado: int
    comision: int
    liquidacion: int
    precio_venta_final: int | None = None
    fecha_recepcion: date
    fecha_venta: date | None = None


class RegistrarVentaIn(BaseModel):
    model_config = ConfigDict(strict=True)

    vendedor_user_id: int
    precio_venta_final: int = Field(ge=0)


class EquipoVentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str


class VehiculoGlobalLookupItemOut(BaseModel):
    id: int
    tenant_id: int
    tenant_nombre: str
    ppu: str
    marca: str
    modelo: str
    anio: int
    n_motor: str | None = None
    n_chasis: str | None = None
    estado_code: str


class VehiculoGlobalLookupOut(BaseModel):
    found: bool
    vehiculo: VehiculoGlobalLookupItemOut | None = None


class VehiculoChecklistOut(BaseModel):
    checklist_item_id: int
    item: str
    tipo: str
    presente: bool
    estado: str | None = None
    fecha_vencimiento: date | None = None
    observacion: str | None = None


class VehiculoDetailOut(VehiculoOut):
    n_motor: str | None = None
    n_chasis: str | None = None
    vigencia_dias: int
    exclusividad_abono: int
    cliente_detalle: ClienteOut
    checklist: list[VehiculoChecklistOut]

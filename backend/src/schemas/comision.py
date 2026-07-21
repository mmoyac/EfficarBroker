from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ParametrosComisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pool_pct: int
    captacion_pct: int
    venta_pct: int


class ParametrosComisionIn(BaseModel):
    model_config = ConfigDict(strict=True)

    pool_pct: int = Field(ge=0, le=100)
    captacion_pct: int = Field(ge=0, le=100)
    venta_pct: int = Field(ge=0, le=100)


class ComisionOut(BaseModel):
    id: int
    acta_id: int
    ppu: str
    vehiculo: str
    cliente: str
    beneficiario: str
    tipo: str
    tipo_code: str
    monto: int
    estado_pago: str
    estado_pago_code: str
    fecha_generacion: datetime
    orden_pago_id: int | None = None
    fecha_venta: date | None = None


class ComisionesResumenOut(BaseModel):
    total: int
    total_pendiente: int
    total_pagada: int
    items: list[ComisionOut]


class OrdenPagoCreate(BaseModel):
    # Sin strict: permite coerción de fechas ISO (string -> date) enviadas por el frontend.
    beneficiario_user_id: int
    periodo_desde: date
    periodo_hasta: date
    fecha_pago: date
    monto_base: int = Field(default=0, ge=0)


class OrdenPagoOut(BaseModel):
    id: int
    beneficiario: str
    beneficiario_user_id: int
    periodo_desde: date
    periodo_hasta: date
    fecha_pago: date
    monto_comisiones: int
    monto_base: int
    monto_total: int
    comisiones: list[ComisionOut] = []


class EstadoResultadoOut(BaseModel):
    desde: date | None = None
    hasta: date | None = None
    ventas_cantidad: int
    monto_transado: int
    comision_empresa: int
    comisiones_ejecutivos: int
    margen_corretaje: int
    abonos_retenidos: int
    abonos_comprometidos: int

import { api } from "@/services/api";

export interface ParametrosComision {
  pool_pct: number;
  captacion_pct: number;
  venta_pct: number;
}

export interface Comision {
  id: number;
  acta_id: number;
  ppu: string;
  vehiculo: string;
  cliente: string;
  beneficiario: string;
  tipo: string;
  tipo_code: string;
  monto: number;
  estado_pago: string;
  estado_pago_code: string;
  fecha_generacion: string;
  orden_pago_id: number | null;
  fecha_venta: string | null;
}

export interface ComisionesResumen {
  total: number;
  total_pendiente: number;
  total_pagada: number;
  items: Comision[];
}

export interface OrdenPago {
  id: number;
  beneficiario: string;
  beneficiario_user_id: number;
  periodo_desde: string;
  periodo_hasta: string;
  fecha_pago: string;
  monto_comisiones: number;
  monto_base: number;
  monto_total: number;
  comisiones: Comision[];
}

export interface EstadoResultado {
  desde: string | null;
  hasta: string | null;
  ventas_cantidad: number;
  monto_transado: number;
  comision_empresa: number;
  comisiones_ejecutivos: number;
  margen_corretaje: number;
  abonos_retenidos: number;
  abonos_comprometidos: number;
}

export async function getParametros(): Promise<ParametrosComision> {
  const { data } = await api.get<ParametrosComision>("/parametros-comision");
  return data;
}

export async function updateParametros(input: ParametrosComision): Promise<ParametrosComision> {
  const { data } = await api.patch<ParametrosComision>("/parametros-comision", input);
  return data;
}

export async function listComisiones(params: { mine?: boolean; desde?: string; hasta?: string; estado_pago?: string } = {}): Promise<ComisionesResumen> {
  const { data } = await api.get<ComisionesResumen>("/comisiones", { params });
  return data;
}

export async function listOrdenesPago(params: { mine?: boolean } = {}): Promise<OrdenPago[]> {
  const { data } = await api.get<OrdenPago[]>("/ordenes-pago", { params });
  return data;
}

export async function crearOrdenPago(input: {
  beneficiario_user_id: number;
  periodo_desde: string;
  periodo_hasta: string;
  fecha_pago: string;
  monto_base: number;
}): Promise<OrdenPago> {
  const { data } = await api.post<OrdenPago>("/ordenes-pago", input);
  return data;
}

export async function getEstadoResultado(params: { desde?: string; hasta?: string } = {}): Promise<EstadoResultado> {
  const { data } = await api.get<EstadoResultado>("/estado-resultado", { params });
  return data;
}

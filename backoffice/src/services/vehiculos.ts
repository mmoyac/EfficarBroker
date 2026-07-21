import { api } from "@/services/api";
import type {
  ActaHistorialItem,
  ChecklistItem,
  ClienteLookup,
  CodeNombre,
  Combustible,
  Comuna,
  EquipoVenta,
  TipoComision,
  TipoVehiculo,
  VehiculoFicha,
  VehiculoGlobalLookup,
  VehiculoLookup,
  VehiculoMarcaCatalog,
  VehiculoModeloCatalog,
  VehiculoUpdateInput,
  VehiculoVersionCatalog,
} from "@/types";

// ---- Catálogos ----

export async function listChecklistItems(): Promise<ChecklistItem[]> {
  const { data } = await api.get<ChecklistItem[]>("/checklist-items");
  return data;
}

export async function listComunas(): Promise<Comuna[]> {
  const { data } = await api.get<Comuna[]>("/comunas");
  return data;
}

export async function listTiposVehiculo(): Promise<TipoVehiculo[]> {
  const { data } = await api.get<TipoVehiculo[]>("/tipos-vehiculo");
  return data;
}

export async function listCombustibles(): Promise<Combustible[]> {
  const { data } = await api.get<Combustible[]>("/combustibles");
  return data;
}

export async function listColores(): Promise<CodeNombre[]> {
  const { data } = await api.get<CodeNombre[]>("/colores");
  return data;
}

export async function listEstadosChecklist(): Promise<CodeNombre[]> {
  const { data } = await api.get<CodeNombre[]>("/estados-checklist");
  return data;
}

export async function listTiposComision(): Promise<TipoComision[]> {
  const { data } = await api.get<TipoComision[]>("/tipos-comision");
  return data;
}

export async function listVehiculoMarcas(): Promise<VehiculoMarcaCatalog[]> {
  const { data } = await api.get<VehiculoMarcaCatalog[]>("/vehiculo-marcas");
  return data;
}

export async function listVehiculoModelos(marcaId: number): Promise<VehiculoModeloCatalog[]> {
  const { data } = await api.get<VehiculoModeloCatalog[]>("/vehiculo-modelos", { params: { marca_id: marcaId } });
  return data;
}

export async function listVehiculoVersiones(modeloId: number): Promise<VehiculoVersionCatalog[]> {
  const { data } = await api.get<VehiculoVersionCatalog[]>("/vehiculo-versiones", { params: { modelo_id: modeloId } });
  return data;
}

export async function listEquipoVentas(sucursalId?: number): Promise<EquipoVenta[]> {
  const { data } = await api.get<EquipoVenta[]>("/equipo-ventas", {
    params: sucursalId ? { sucursal_id: sucursalId } : {},
  });
  return data;
}

// ---- Lookups ----

export async function findClienteByRut(rut: string): Promise<ClienteLookup> {
  const { data } = await api.get<ClienteLookup>("/vehiculos/lookup/cliente", { params: { rut } });
  return data;
}

/** Lookup por PPU dentro del tenant, para precargar el formulario y detectar reingresos. */
export async function lookupVehiculoByPpu(ppu: string): Promise<VehiculoLookup> {
  const { data } = await api.get<VehiculoLookup>("/vehiculos/lookup", { params: { ppu } });
  return data;
}

export async function findVehiculoGlobalByPpu(ppu: string): Promise<VehiculoGlobalLookup> {
  const { data } = await api.get<VehiculoGlobalLookup>("/vehiculos/lookup/vehiculo-global", { params: { ppu } });
  return data;
}

// ---- Fichas y mantenedor ----

export async function listVehiculos(q?: string): Promise<VehiculoFicha[]> {
  const { data } = await api.get<VehiculoFicha[]>("/vehiculos", { params: q ? { q } : {} });
  return data;
}

export async function getVehiculo(id: number): Promise<VehiculoFicha> {
  const { data } = await api.get<VehiculoFicha>(`/vehiculos/${id}`);
  return data;
}

export async function getVehiculoActas(id: number): Promise<ActaHistorialItem[]> {
  const { data } = await api.get<ActaHistorialItem[]>(`/vehiculos/${id}/actas`);
  return data;
}

export async function updateVehiculo(id: number, input: VehiculoUpdateInput): Promise<VehiculoFicha> {
  const { data } = await api.patch<VehiculoFicha>(`/vehiculos/${id}`, input);
  return data;
}

export async function deleteVehiculo(id: number): Promise<void> {
  await api.delete(`/vehiculos/${id}`);
}

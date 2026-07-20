import { api } from "@/services/api";
import type {
  ActaCreateInput,
  ChecklistItem,
  ClienteLookup,
  Combustible,
  Comuna,
  EquipoVenta,
  TipoComision,
  TipoVehiculo,
  VehiculoMarcaCatalog,
  VehiculoModeloCatalog,
  VehiculoUpdateInput,
  VehiculoVersionCatalog,
  Vehiculo,
  VehiculoDetail,
  VehiculoGlobalLookup,
} from "@/types";

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

export async function createActa(input: ActaCreateInput): Promise<VehiculoDetail> {
  const { data } = await api.post<VehiculoDetail>("/vehiculos", input);
  return data;
}

export async function findClienteByRut(rut: string): Promise<ClienteLookup> {
  const { data } = await api.get<ClienteLookup>("/vehiculos/lookup/cliente", { params: { rut } });
  return data;
}

export async function findVehiculoGlobalByPpu(ppu: string): Promise<VehiculoGlobalLookup> {
  const { data } = await api.get<VehiculoGlobalLookup>("/vehiculos/lookup/vehiculo-global", { params: { ppu } });
  return data;
}

export async function listVehiculos(mine = false): Promise<Vehiculo[]> {
  const { data } = await api.get<Vehiculo[]>("/vehiculos", { params: { mine } });
  return data;
}

export async function listVehiculosDerivados(): Promise<Vehiculo[]> {
  const { data } = await api.get<Vehiculo[]>("/vehiculos", { params: { derivadas: true } });
  return data;
}

export async function getVehiculo(id: number): Promise<VehiculoDetail> {
  const { data } = await api.get<VehiculoDetail>(`/vehiculos/${id}`);
  return data;
}

export async function deleteVehiculo(id: number): Promise<void> {
  await api.delete(`/vehiculos/${id}`);
}

export async function updateVehiculo(id: number, input: VehiculoUpdateInput): Promise<VehiculoDetail> {
  const { data } = await api.patch<VehiculoDetail>(`/vehiculos/${id}`, input);
  return data;
}

export async function aceptarTerminos(id: number): Promise<VehiculoDetail> {
  const { data } = await api.post<VehiculoDetail>(`/vehiculos/${id}/aceptar-terminos`, {});
  return data;
}

export async function listEquipoVentas(): Promise<EquipoVenta[]> {
  const { data } = await api.get<EquipoVenta[]>("/equipo-ventas");
  return data;
}

export async function registrarVenta(
  id: number,
  vendedorUserId: number,
  precioVentaFinal: number,
): Promise<VehiculoDetail> {
  const { data } = await api.post<VehiculoDetail>(`/vehiculos/${id}/registrar-venta`, {
    vendedor_user_id: vendedorUserId,
    precio_venta_final: precioVentaFinal,
  });
  return data;
}

export async function downloadDocumentoFirma(id: number): Promise<Blob> {
  const { data } = await api.get<Blob>(`/vehiculos/${id}/documento-firma`, {
    responseType: "blob",
  });
  return data;
}

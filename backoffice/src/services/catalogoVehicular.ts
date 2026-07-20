import { api } from "@/services/api";
import type {
  VehiculoMarcaCatalog,
  VehiculoModeloCatalog,
  VehiculoVersionCatalog,
} from "@/types";

export async function createVehiculoMarca(nombre: string): Promise<VehiculoMarcaCatalog> {
  const { data } = await api.post<VehiculoMarcaCatalog>("/vehiculo-marcas", { nombre });
  return data;
}

export async function updateVehiculoMarca(id: number, nombre: string): Promise<VehiculoMarcaCatalog> {
  const { data } = await api.patch<VehiculoMarcaCatalog>(`/vehiculo-marcas/${id}`, { nombre });
  return data;
}

export async function deleteVehiculoMarca(id: number): Promise<void> {
  await api.delete(`/vehiculo-marcas/${id}`);
}

export async function createVehiculoModelo(
  marcaId: number,
  nombre: string,
): Promise<VehiculoModeloCatalog> {
  const { data } = await api.post<VehiculoModeloCatalog>("/vehiculo-modelos", {
    marca_id: marcaId,
    nombre,
  });
  return data;
}

export async function updateVehiculoModelo(
  id: number,
  marcaId: number,
  nombre: string,
): Promise<VehiculoModeloCatalog> {
  const { data } = await api.patch<VehiculoModeloCatalog>(`/vehiculo-modelos/${id}`, {
    marca_id: marcaId,
    nombre,
  });
  return data;
}

export async function deleteVehiculoModelo(id: number): Promise<void> {
  await api.delete(`/vehiculo-modelos/${id}`);
}

export async function createVehiculoVersion(
  modeloId: number,
  nombre: string,
): Promise<VehiculoVersionCatalog> {
  const { data } = await api.post<VehiculoVersionCatalog>("/vehiculo-versiones", {
    modelo_id: modeloId,
    nombre,
  });
  return data;
}

export async function updateVehiculoVersion(
  id: number,
  modeloId: number,
  nombre: string,
): Promise<VehiculoVersionCatalog> {
  const { data } = await api.patch<VehiculoVersionCatalog>(`/vehiculo-versiones/${id}`, {
    modelo_id: modeloId,
    nombre,
  });
  return data;
}

export async function deleteVehiculoVersion(id: number): Promise<void> {
  await api.delete(`/vehiculo-versiones/${id}`);
}

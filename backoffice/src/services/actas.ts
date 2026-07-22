import { api } from "@/services/api";
import type {
  Acta,
  ActaCreateInput,
  ActaDetail,
  ActaFoto,
  ActaUpdateInput,
  AbonoResumen,
  ChecklistEntryInput,
} from "@/types";

export async function createActa(input: ActaCreateInput): Promise<ActaDetail> {
  const { data } = await api.post<ActaDetail>("/actas", input);
  return data;
}

export async function listActas(params: { mine?: boolean; derivadas?: boolean } = {}): Promise<Acta[]> {
  const { data } = await api.get<Acta[]>("/actas", { params });
  return data;
}

export async function getActa(id: number): Promise<ActaDetail> {
  const { data } = await api.get<ActaDetail>(`/actas/${id}`);
  return data;
}

export async function updateActa(id: number, input: ActaUpdateInput): Promise<ActaDetail> {
  const { data } = await api.patch<ActaDetail>(`/actas/${id}`, input);
  return data;
}

export async function deleteActa(id: number): Promise<void> {
  await api.delete(`/actas/${id}`);
}

export interface RecepcionarInput {
  n_motor?: string | null;
  n_chasis?: string | null;
  color_id?: number | null;
  km_ingreso?: number | null;
  checklist?: ChecklistEntryInput[];
}

export async function recepcionar(id: number, input: RecepcionarInput): Promise<ActaDetail> {
  const { data } = await api.post<ActaDetail>(`/actas/${id}/recepcionar`, input);
  return data;
}

export async function registrarVenta(
  id: number,
  vendedorUserId: number,
  precioVentaFinal: number,
): Promise<ActaDetail> {
  const { data } = await api.post<ActaDetail>(`/actas/${id}/registrar-venta`, {
    vendedor_user_id: vendedorUserId,
    precio_venta_final: precioVentaFinal,
  });
  return data;
}

export async function cerrarSinVenta(
  id: number,
  motivoCierreId: number,
  observacion: string | null,
): Promise<ActaDetail> {
  const { data } = await api.post<ActaDetail>(`/actas/${id}/cerrar-sin-venta`, {
    motivo_cierre_id: motivoCierreId,
    observacion: observacion,
  });
  return data;
}

export async function downloadDocumentoFirma(id: number): Promise<Blob> {
  const { data } = await api.get<Blob>(`/actas/${id}/documento-firma`, {
    responseType: "blob",
  });
  return data;
}

export async function getResumenAbonos(): Promise<AbonoResumen> {
  const { data } = await api.get<AbonoResumen>("/abonos/resumen");
  return data;
}

// ---- Galería multimedia del acta (fotos + video 360) ----

export async function listFotos(actaId: number): Promise<ActaFoto[]> {
  const { data } = await api.get<ActaFoto[]>(`/actas/${actaId}/fotos`);
  return data;
}

export async function agregarFotoUrl(actaId: number, url: string): Promise<ActaFoto> {
  const { data } = await api.post<ActaFoto>(`/actas/${actaId}/fotos`, { url });
  return data;
}

export async function subirFoto(actaId: number, file: File): Promise<ActaFoto> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<ActaFoto>(`/actas/${actaId}/fotos/upload`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function actualizarFoto(
  actaId: number,
  fotoId: number,
  input: { orden?: number; es_principal?: boolean },
): Promise<ActaFoto> {
  const { data } = await api.patch<ActaFoto>(`/actas/${actaId}/fotos/${fotoId}`, input);
  return data;
}

export async function eliminarFoto(actaId: number, fotoId: number): Promise<void> {
  await api.delete(`/actas/${actaId}/fotos/${fotoId}`);
}

export async function actualizarVideo(
  actaId: number,
  videoYoutubeUrl: string | null,
): Promise<{ video_youtube_url: string | null }> {
  const { data } = await api.patch<{ video_youtube_url: string | null }>(
    `/actas/${actaId}/video`,
    { video_youtube_url: videoYoutubeUrl },
  );
  return data;
}

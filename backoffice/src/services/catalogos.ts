import { api } from "@/services/api";
import type { CodeNombre } from "@/types";

export async function listMotivosCierre(): Promise<CodeNombre[]> {
  const { data } = await api.get<CodeNombre[]>("/motivos-cierre-acta");
  return data;
}

export async function listEstadosAbono(): Promise<CodeNombre[]> {
  const { data } = await api.get<CodeNombre[]>("/estados-abono");
  return data;
}

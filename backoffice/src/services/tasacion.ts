import { api } from "@/services/api";
import type {
  TasacionProspecto,
  TasacionSimularInput,
  TasacionSimularResult,
} from "@/types";

export async function simularTasacion(input: TasacionSimularInput): Promise<TasacionSimularResult> {
  const { data } = await api.post<TasacionSimularResult>("/tasacion/simular", input);
  return data;
}

export async function listTasacionProspectos(mine = true): Promise<TasacionProspecto[]> {
  const { data } = await api.get<TasacionProspecto[]>("/tasacion/prospectos", { params: { mine } });
  return data;
}

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listTasacionProspectos, simularTasacion } from "@/services/tasacion";
import { listVehiculoMarcas, listVehiculoModelos, listVehiculoVersiones } from "@/services/vehiculos";
import type { TasacionProspecto, TasacionSimularResult } from "@/types";

export default function Tasacion() {
  const [ppu, setPpu] = useState("");
  const [referenciaUrl, setReferenciaUrl] = useState("");
  const [marcaId, setMarcaId] = useState<number | "">("");
  const [modeloId, setModeloId] = useState<number | "">("");
  const [versionId, setVersionId] = useState<number | "">("");
  const [anio, setAnio] = useState("");
  const [km, setKm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<TasacionSimularResult | null>(null);
  const queryClient = useQueryClient();

  const prospectosQ = useQuery({
    queryKey: ["tasacion-prospectos", "mine"],
    queryFn: () => listTasacionProspectos(true),
  });

  const marcasQ = useQuery({
    queryKey: ["tasacion-catalog", "marcas"],
    queryFn: listVehiculoMarcas,
  });

  const modelosQ = useQuery({
    queryKey: ["tasacion-catalog", "modelos", marcaId],
    queryFn: () => listVehiculoModelos(Number(marcaId)),
    enabled: marcaId !== "",
  });

  const versionesQ = useQuery({
    queryKey: ["tasacion-catalog", "versiones", modeloId],
    queryFn: () => listVehiculoVersiones(Number(modeloId)),
    enabled: modeloId !== "",
  });

  const mut = useMutation({
    mutationFn: simularTasacion,
    onSuccess: (data) => {
      setResultado(data);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["tasacion-prospectos", "mine"] });
    },
    onError: (e: unknown) => setError(extractError(e)),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const ppuNorm = ppu.trim().toUpperCase();
    const anioNum = Number(anio);
    const kmNum = Number(km);

    if (ppuNorm.length < 4) {
      setError("Ingresa una patente válida.");
      return;
    }
    if (marcaId === "" || modeloId === "") {
      setError("Selecciona marca y modelo del vehículo.");
      return;
    }
    if (versionId === "") {
      setError("Selecciona una versión del vehículo.");
      return;
    }
    if (!Number.isFinite(anioNum) || anioNum < 1900 || anioNum > 2100) {
      setError("Ingresa un año válido.");
      return;
    }
    if (!Number.isFinite(kmNum) || kmNum < 0) {
      setError("Ingresa un kilometraje válido.");
      return;
    }

    mut.mutate({
      ppu: ppuNorm,
      version_id: Number(versionId),
      anio: anioNum,
      km: kmNum,
      referencia_url: referenciaUrl.trim() || null,
    });
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-ink">Tasación Rápida</h1>
        <p className="mt-1 text-sm text-brand-muted">
          Según el spec M1: ingresa PPU y kilometraje para estimar rangos de precio.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="rounded-xl border border-brand-surface-2 bg-white p-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Patente (PPU)</span>
            <input
              required
              value={ppu}
              onChange={(e) => setPpu(e.target.value)}
              className={inputCls}
              placeholder="Ej: AB1234"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Marca</span>
            <select
              required
              value={marcaId}
              onChange={(e) => {
                setMarcaId(e.target.value === "" ? "" : Number(e.target.value));
                setModeloId("");
                setVersionId("");
              }}
              className={inputCls}
            >
              <option value="" disabled>Seleccionar marca</option>
              {marcasQ.data?.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Modelo</span>
            <select
              required
              value={modeloId}
              onChange={(e) => {
                setModeloId(e.target.value === "" ? "" : Number(e.target.value));
                setVersionId("");
              }}
              className={inputCls}
              disabled={marcaId === ""}
            >
              <option value="" disabled>Seleccionar modelo</option>
              {modelosQ.data?.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Versión</span>
            <select
              required
              value={versionId}
              onChange={(e) => setVersionId(e.target.value === "" ? "" : Number(e.target.value))}
              className={inputCls}
              disabled={modeloId === ""}
            >
              <option value="" disabled>Seleccionar versión</option>
              {versionesQ.data?.map((v) => (
                <option key={v.id} value={v.id}>{v.nombre}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Año</span>
            <input
              required
              type="number"
              min={1900}
              max={2100}
              value={anio}
              onChange={(e) => setAnio(e.target.value)}
              className={inputCls}
              placeholder="Ej: 2020"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Kilometraje</span>
            <input
              required
              type="number"
              min={0}
              value={km}
              onChange={(e) => setKm(e.target.value)}
              className={inputCls}
              placeholder="Ej: 85000"
            />
          </label>

          <label className="block sm:col-span-2 lg:col-span-4">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Link directo Chileautos (opcional)</span>
            <input
              type="url"
              value={referenciaUrl}
              onChange={(e) => setReferenciaUrl(e.target.value)}
              className={inputCls}
              placeholder="https://www.chileautos.cl/vehiculos/..."
            />
          </label>
        </div>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            disabled={mut.isPending}
            className="rounded-lg bg-brand-accent px-5 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60"
          >
            {mut.isPending ? "Calculando..." : "Simular Tasación"}
          </button>
        </div>
      </form>

      {resultado && (
        <section className="rounded-xl border border-brand-surface-2 bg-white p-5">
          <h2 className="mb-4 font-semibold text-brand-ink">Resultado de Tasación</h2>
          <p className="mb-3 text-xs text-brand-muted">Prospecto guardado con ID #{resultado.prospecto_id}.</p>
          {resultado.fuente.startsWith("fallback_") && (
            <p className="mb-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              Resultado en modo contingencia (baja confianza). Recomendado validar con comparables manuales.
            </p>
          )}
          <div className="grid gap-3 sm:grid-cols-3">
            <PriceCard label="Precio Mercado" value={resultado.precio_mercado} />
            <PriceCard label="Precio Retoma" value={resultado.precio_retoma} />
            <PriceCard
              label="Precio Publicación Sugerido"
              value={resultado.precio_publicacion_sugerido}
            />
          </div>
          <p className="mt-4 text-xs text-brand-muted">
            Fuente: {resultado.fuente} ({resultado.sample_size} referencias). {resultado.observacion}
            {resultado.scrape_url ? " Ver referencia: " : ""}
            {resultado.scrape_url ? (
              <a
                href={resultado.scrape_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-brand-accent hover:underline"
              >
                abrir aviso
              </a>
            ) : null}
          </p>
        </section>
      )}

      <section className="rounded-xl border border-brand-surface-2 bg-white p-5">
        <h2 className="mb-4 font-semibold text-brand-ink">Mis Prospectos Recientes</h2>
        {prospectosQ.isLoading && <p className="text-sm text-brand-muted">Cargando prospectos...</p>}
        {prospectosQ.isError && <p className="text-sm text-red-600">No se pudieron cargar tus prospectos.</p>}
        {!prospectosQ.isLoading && !prospectosQ.isError && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-brand-surface-2 text-brand-muted">
                  <th className="py-2 pr-3">ID</th>
                  <th className="py-2 pr-3">Patente</th>
                  <th className="py-2 pr-3">KM</th>
                  <th className="py-2 pr-3">Mercado</th>
                  <th className="py-2 pr-3">Fuente</th>
                  <th className="py-2 pr-3">Estado</th>
                </tr>
              </thead>
              <tbody>
                {(prospectosQ.data ?? []).slice(0, 8).map((p) => (
                  <ProspectoRow key={p.id} p={p} />
                ))}
                {(prospectosQ.data ?? []).length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-3 text-brand-muted">
                      Aún no tienes prospectos de tasación.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function ProspectoRow({ p }: { p: TasacionProspecto }) {
  return (
    <tr className="border-b border-brand-surface-2/70 text-brand-ink">
      <td className="py-2 pr-3">#{p.id}</td>
      <td className="py-2 pr-3 font-medium">{p.ppu}</td>
      <td className="py-2 pr-3">{p.km.toLocaleString("es-CL")}</td>
      <td className="py-2 pr-3">{formatClp(p.precio_mercado)}</td>
      <td className="py-2 pr-3">{p.fuente}</td>
      <td className="py-2 pr-3">{p.estado_code}</td>
    </tr>
  );
}

function PriceCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="rounded-lg border border-brand-surface-2 bg-brand-surface px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-brand-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-brand-ink">{formatClp(value)}</p>
    </article>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function formatClp(value: number): string {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(value);
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo calcular la tasación.";
}

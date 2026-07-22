import { useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  actualizarFoto,
  actualizarVideo,
  agregarFotoUrl,
  eliminarFoto,
  getActa,
  listFotos,
  subirFoto,
} from "@/services/actas";
import { assetUrl } from "@/services/api";
import { getVehiculoActas } from "@/services/vehiculos";
import { useAuth } from "@/context/AuthContext";
import type { ActaDetail, ActaFoto } from "@/types";

const clp = (n: number | null | undefined) => `$${(n ?? 0).toLocaleString("es-CL")}`;
const fmt = (d: string | null) => (d ? new Date(d + "T00:00:00").toLocaleDateString("es-CL") : "—");

const TRANSVERSALES = new Set(["Management", "TenantAdmin", "SuperAdmin"]);

function youtubeId(url: string | null): string | null {
  if (!url) return null;
  const m = url.match(/[?&]v=([A-Za-z0-9_-]{11})/) ?? url.match(/youtu\.be\/([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : "No se pudo completar la acción.";
}

export default function ActaDetalle() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const actaId = Number(id);

  const actaQ = useQuery({ queryKey: ["acta", actaId], queryFn: () => getActa(actaId) });
  const historialQ = useQuery({
    queryKey: ["vehiculo-actas", actaQ.data?.vehiculo_id],
    queryFn: () => getVehiculoActas(actaQ.data!.vehiculo_id),
    enabled: actaQ.data != null,
  });

  if (actaQ.isLoading) return <p className="text-brand-muted">Cargando…</p>;
  if (actaQ.isError || !actaQ.data) return <p className="text-red-600">No se pudo cargar el acta.</p>;

  const a = actaQ.data;
  const v = a.vehiculo;
  const anteriores = (historialQ.data ?? []).filter((h) => h.id !== a.id);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <button onClick={() => navigate("/actas")} className="text-sm text-brand-muted hover:underline">
        ← Volver a actas
      </button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">
            {v.marca} {v.modelo} <span className="font-mono text-brand-muted">{a.ppu}</span>
          </h1>
          <p className="text-sm text-brand-muted">
            {a.estado} · recepción {fmt(a.fecha_recepcion)} · captó {a.captador}
          </p>
        </div>
      </div>

      <Section title="Vehículo">
        <Grid>
          <Field label="Marca / Modelo" value={`${v.marca} ${v.modelo}`} />
          <Field label="Versión" value={v.version} />
          <Field label="Año" value={String(v.anio)} />
          <Field label="Color" value={v.color ?? "—"} />
          <Field label="N° Motor" value={v.n_motor ?? "—"} />
          <Field label="N° Chasis" value={v.n_chasis ?? "—"} />
          <Field label="Kilometraje (esta recepción)" value={a.km_ingreso.toLocaleString("es-CL")} />
        </Grid>
      </Section>

      <GaleriaSection acta={a} />

      <Section title="Cliente (dueño en esta recepción)">
        <Grid>
          <Field label="Nombre" value={a.cliente_detalle.nombre} />
          <Field label="RUT" value={a.cliente_detalle.rut} />
          <Field label="Email" value={a.cliente_detalle.email ?? "—"} />
          <Field label="Teléfono" value={a.cliente_detalle.telefono ?? "—"} />
          <Field label="Domicilio" value={a.cliente_detalle.domicilio ?? "—"} />
          <Field label="Comuna" value={a.cliente_detalle.comuna ?? "—"} />
        </Grid>
      </Section>

      <Section title="Orden de venta">
        <Grid>
          <Field label="Precio pactado" value={clp(a.precio_venta_pactado)} />
          <Field label="Tipo de comisión" value={a.tipo_comision ?? "—"} />
          <Field label="Comisión" value={clp(a.comision)} />
          <Field label="Abono exclusividad" value={clp(a.exclusividad_abono)} />
          <Field label="Comisión a cobrar al cierre" value={clp(a.comision_neta)} hint="ya descontado el abono" />
          <Field label="Estado del abono" value={a.estado_abono} />
          <Field label="Vigencia" value={`${a.vigencia_dias} días`} />
          <Field label="Sucursal de venta" value={a.sucursal_venta + (a.derivado ? " (derivada)" : "")} />
          <Field label="Vendedor / ejecutivo" value={a.vendedor ?? `${a.captador} (captador)`} />
        </Grid>
      </Section>

      {a.observaciones && (
        <Section title="Observaciones">
          <p className="text-sm text-brand-ink whitespace-pre-wrap">{a.observaciones}</p>
        </Section>
      )}

      <Section title="Checklist de recepción">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-3 py-2 font-medium">Punto</th>
                <th className="px-3 py-2 font-medium">Presente</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2 font-medium">Vencimiento</th>
                <th className="px-3 py-2 font-medium">Observación</th>
              </tr>
            </thead>
            <tbody>
              {a.checklist.map((c) => (
                <tr key={c.checklist_item_id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-3 py-2">{c.item}</td>
                  <td className="px-3 py-2">{c.presente ? "Sí" : "No"}</td>
                  <td className="px-3 py-2">{c.estado ?? "—"}</td>
                  <td className="px-3 py-2">{fmt(c.fecha_vencimiento)}</td>
                  <td className="px-3 py-2 text-brand-muted">{c.observacion ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Historial de recepciones de este vehículo">
        {anteriores.length === 0 ? (
          <p className="text-sm text-brand-muted">Es la primera vez que este auto se corretó en el tenant.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                  <th className="px-3 py-2 font-medium">Recepción</th>
                  <th className="px-3 py-2 font-medium">Dueño</th>
                  <th className="px-3 py-2 font-medium">Captador</th>
                  <th className="px-3 py-2 font-medium">Estado</th>
                  <th className="px-3 py-2 font-medium">Venta</th>
                </tr>
              </thead>
              <tbody>
                {anteriores.map((h) => (
                  <tr
                    key={h.id}
                    onClick={() => navigate(`/actas/${h.id}`)}
                    className="cursor-pointer border-b border-brand-surface-2 last:border-0 hover:bg-brand-surface/60"
                  >
                    <td className="px-3 py-2">{fmt(h.fecha_recepcion)}</td>
                    <td className="px-3 py-2">{h.cliente}</td>
                    <td className="px-3 py-2">{h.captador}</td>
                    <td className="px-3 py-2">{h.estado_code}{h.cerrada ? " (cerrada)" : ""}</td>
                    <td className="px-3 py-2">
                      {h.precio_venta_final != null ? `${clp(h.precio_venta_final)} · ${fmt(h.fecha_venta)}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

function GaleriaSection({ acta }: { acta: ActaDetail }) {
  const { user } = useAuth();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");
  const [video, setVideo] = useState(acta.video_youtube_url ?? "");
  const [error, setError] = useState<string | null>(null);

  const esTransversal = TRANSVERSALES.has(user?.role_code ?? "");
  const esCaptadorOVendedor =
    user?.id === acta.captador_user_id || user?.id === acta.vendedor_user_id;
  const esEquipoDerivada = acta.derivado && user?.sucursal_id === acta.sucursal_venta_id;
  const puedeGestionar =
    esTransversal || (!acta.cerrada && (esCaptadorOVendedor || esEquipoDerivada));

  const fotosQ = useQuery({ queryKey: ["acta-fotos", acta.id], queryFn: () => listFotos(acta.id) });
  const fotos = fotosQ.data ?? [];

  const refresh = () => qc.invalidateQueries({ queryKey: ["acta-fotos", acta.id] });
  const onError = (e: unknown) => setError(extractError(e));

  const addUrlMut = useMutation({
    mutationFn: () => agregarFotoUrl(acta.id, url.trim()),
    onSuccess: () => { setUrl(""); setError(null); refresh(); },
    onError,
  });
  const uploadMut = useMutation({
    mutationFn: (file: File) => subirFoto(acta.id, file),
    onSuccess: () => { setError(null); refresh(); },
    onError,
  });
  const delMut = useMutation({
    mutationFn: (fotoId: number) => eliminarFoto(acta.id, fotoId),
    onSuccess: () => { setError(null); refresh(); },
    onError,
  });
  const principalMut = useMutation({
    mutationFn: (fotoId: number) => actualizarFoto(acta.id, fotoId, { es_principal: true }),
    onSuccess: () => { setError(null); refresh(); },
    onError,
  });
  const moverMut = useMutation({
    mutationFn: async ({ foto, vecino }: { foto: ActaFoto; vecino: ActaFoto }) => {
      await actualizarFoto(acta.id, foto.id, { orden: vecino.orden });
      await actualizarFoto(acta.id, vecino.id, { orden: foto.orden });
    },
    onSuccess: () => { setError(null); refresh(); },
    onError,
  });
  const videoMut = useMutation({
    mutationFn: () => actualizarVideo(acta.id, video.trim() || null),
    onSuccess: (r) => {
      setVideo(r.video_youtube_url ?? "");
      setError(null);
      qc.invalidateQueries({ queryKey: ["acta", acta.id] });
    },
    onError,
  });

  const vid = youtubeId(acta.video_youtube_url);

  return (
    <Section title="Galería y video (publicación)">
      {!puedeGestionar && (
        <p className="mb-3 text-xs text-brand-muted">
          Material visual de esta publicación. Solo lectura para tu rol.
        </p>
      )}

      {puedeGestionar && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) uploadMut.mutate(file);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploadMut.isPending}
            className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60"
          >
            {uploadMut.isPending ? "Subiendo…" : "Subir foto"}
          </button>
          <form
            onSubmit={(e) => { e.preventDefault(); if (url.trim()) addUrlMut.mutate(); }}
            className="flex flex-1 gap-2"
          >
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="…o pega una URL del cloud (https://…)"
              className={inputCls}
            />
            <button
              type="submit"
              disabled={addUrlMut.isPending || !url.trim()}
              className="rounded-lg border border-brand-surface-2 px-3 py-2 text-sm hover:bg-brand-surface disabled:opacity-60"
            >
              Agregar URL
            </button>
          </form>
        </div>
      )}

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

      {fotosQ.isLoading && <p className="text-sm text-brand-muted">Cargando fotos…</p>}
      {fotos.length === 0 && !fotosQ.isLoading && (
        <p className="rounded-lg border border-dashed border-brand-surface-2 p-6 text-center text-sm text-brand-muted">
          Sin fotos. {puedeGestionar ? "Sube una o pega una URL del cloud." : ""}
        </p>
      )}

      {fotos.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {fotos.map((f, i) => (
            <div
              key={f.id}
              className={`group relative overflow-hidden rounded-lg border ${f.es_principal ? "border-brand-accent ring-2 ring-brand-accent/40" : "border-brand-surface-2"}`}
            >
              <img src={assetUrl(f.url)} alt="" className="aspect-[3/2] w-full object-cover" />
              {f.es_principal && (
                <span className="absolute left-1 top-1 rounded bg-brand-accent px-1.5 py-0.5 text-[10px] font-semibold text-black">
                  Principal
                </span>
              )}
              {puedeGestionar && (
                <div className="flex items-center justify-between gap-1 p-1 text-xs">
                  <div className="flex gap-1">
                    <button
                      type="button"
                      title="Mover antes"
                      disabled={i === 0 || moverMut.isPending}
                      onClick={() => moverMut.mutate({ foto: f, vecino: fotos[i - 1] })}
                      className="rounded px-1.5 py-0.5 hover:bg-brand-surface disabled:opacity-30"
                    >←</button>
                    <button
                      type="button"
                      title="Mover después"
                      disabled={i === fotos.length - 1 || moverMut.isPending}
                      onClick={() => moverMut.mutate({ foto: f, vecino: fotos[i + 1] })}
                      className="rounded px-1.5 py-0.5 hover:bg-brand-surface disabled:opacity-30"
                    >→</button>
                  </div>
                  <div className="flex gap-1">
                    {!f.es_principal && (
                      <button
                        type="button"
                        onClick={() => principalMut.mutate(f.id)}
                        className="rounded px-1.5 py-0.5 hover:bg-brand-surface"
                      >Principal</button>
                    )}
                    <button
                      type="button"
                      onClick={() => { if (confirm("¿Eliminar esta foto?")) delMut.mutate(f.id); }}
                      className="rounded px-1.5 py-0.5 text-red-600 hover:bg-red-50"
                    >Eliminar</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Video 360 */}
      <div className="mt-6 border-t border-brand-surface-2 pt-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-brand-muted-2">Video 360 (YouTube)</p>
        {puedeGestionar ? (
          <form
            onSubmit={(e) => { e.preventDefault(); videoMut.mutate(); }}
            className="flex flex-wrap gap-2"
          >
            <input
              value={video}
              onChange={(e) => setVideo(e.target.value)}
              placeholder="https://youtu.be/…"
              className={inputCls}
            />
            <button
              type="submit"
              disabled={videoMut.isPending}
              className="rounded-lg border border-brand-surface-2 px-3 py-2 text-sm hover:bg-brand-surface disabled:opacity-60"
            >
              Guardar video
            </button>
            {acta.video_youtube_url && (
              <button
                type="button"
                onClick={() => { setVideo(""); actualizarVideo(acta.id, null).then(() => qc.invalidateQueries({ queryKey: ["acta", acta.id] })); }}
                className="rounded-lg border border-brand-surface-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Quitar
              </button>
            )}
          </form>
        ) : acta.video_youtube_url ? null : (
          <p className="text-sm text-brand-muted">Sin video.</p>
        )}
        {vid && (
          <a
            href={acta.video_youtube_url ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-block"
          >
            <img
              src={`https://img.youtube.com/vi/${vid}/hqdefault.jpg`}
              alt="Video del vehículo"
              className="w-64 max-w-full rounded-lg border border-brand-surface-2"
            />
          </a>
        )}
      </div>
    </Section>
  );
}

const inputCls =
  "flex-1 rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-brand-surface-2 bg-white p-5">
      <h2 className="mb-4 font-semibold text-brand-ink">{title}</h2>
      {children}
    </section>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{children}</div>;
}

function Field({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-brand-muted-2">{label}</p>
      <p className="text-sm text-brand-ink">{value}</p>
      {hint && <p className="text-xs text-brand-muted-2">{hint}</p>}
    </div>
  );
}

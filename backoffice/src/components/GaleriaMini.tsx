import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { assetUrl } from "@/services/api";
import { listFotos } from "@/services/actas";
import type { Acta } from "@/types";

function youtubeId(url: string | null): string | null {
  if (!url) return null;
  const m = url.match(/[?&]v=([A-Za-z0-9_-]{11})/) ?? url.match(/youtu\.be\/([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}

/** Miniatura de la foto principal + insignias; al hacer clic abre el visor de la galería. */
export default function GaleriaMini({ acta }: { acta: Acta }) {
  const [abierto, setAbierto] = useState(false);
  const tieneMedia = acta.fotos_count > 0 || acta.tiene_video;

  return (
    <>
      <button
        type="button"
        onClick={() => tieneMedia && setAbierto(true)}
        disabled={!tieneMedia}
        title={tieneMedia ? "Ver fotos y video" : "Sin fotos"}
        className={`relative h-10 w-14 shrink-0 ${tieneMedia ? "cursor-pointer" : "cursor-default"}`}
      >
        {!tieneMedia ? (
          <span className="flex h-10 w-14 items-center justify-center rounded-md border border-dashed border-brand-surface-2 text-[10px] text-brand-muted-2">
            sin fotos
          </span>
        ) : acta.foto_principal_url ? (
          <img
            src={assetUrl(acta.foto_principal_url)}
            alt=""
            className="h-10 w-14 rounded-md border border-brand-surface-2 object-cover transition hover:brightness-90"
          />
        ) : (
          <span className="flex h-10 w-14 items-center justify-center rounded-md border border-brand-surface-2 bg-brand-surface text-xs">
            🎥
          </span>
        )}
        {acta.fotos_count > 1 && (
          <span className="absolute -right-1 -top-1 rounded-full bg-brand-ink px-1.5 text-[10px] font-semibold text-white">
            {acta.fotos_count}
          </span>
        )}
        {acta.tiene_video && (
          <span
            title="Con video 360"
            className="absolute -bottom-1 -right-1 rounded-full bg-red-600 px-1 text-[9px] leading-4 text-white"
          >
            ▶
          </span>
        )}
      </button>

      {abierto && <GaleriaModal acta={acta} onClose={() => setAbierto(false)} />}
    </>
  );
}

function GaleriaModal({ acta, onClose }: { acta: Acta; onClose: () => void }) {
  const fotosQ = useQuery({ queryKey: ["acta-fotos", acta.id], queryFn: () => listFotos(acta.id) });
  const fotos = fotosQ.data ?? [];
  const vid = youtubeId(acta.video_youtube_url);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-brand-ink">
              {acta.vehiculo.marca} {acta.vehiculo.modelo}{" "}
              <span className="font-mono text-brand-muted">{acta.ppu}</span>
            </h2>
            <p className="text-sm text-brand-muted">
              {acta.fotos_count} foto{acta.fotos_count === 1 ? "" : "s"}
              {acta.tiene_video ? " · con video 360" : ""}
            </p>
          </div>
          <button onClick={onClose} className="rounded-lg border border-brand-surface-2 px-3 py-1 text-sm hover:bg-brand-surface">
            Cerrar
          </button>
        </div>

        {fotosQ.isLoading && <p className="text-sm text-brand-muted">Cargando fotos…</p>}
        {fotos.length === 0 && !fotosQ.isLoading && (
          <p className="text-sm text-brand-muted">Esta publicación no tiene fotos.</p>
        )}

        {fotos.length > 0 && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {fotos.map((f) => (
              <a
                key={f.id}
                href={assetUrl(f.url)}
                target="_blank"
                rel="noreferrer"
                className={`relative block overflow-hidden rounded-lg border ${f.es_principal ? "border-brand-accent ring-2 ring-brand-accent/40" : "border-brand-surface-2"}`}
              >
                <img src={assetUrl(f.url)} alt="" className="aspect-[3/2] w-full object-cover" />
                {f.es_principal && (
                  <span className="absolute left-1 top-1 rounded bg-brand-accent px-1.5 py-0.5 text-[10px] font-semibold text-black">
                    Principal
                  </span>
                )}
              </a>
            ))}
          </div>
        )}

        {vid && (
          <div className="mt-5 border-t border-brand-surface-2 pt-4">
            <p className="mb-2 text-xs uppercase tracking-wide text-brand-muted-2">Video 360</p>
            <a href={acta.video_youtube_url ?? "#"} target="_blank" rel="noreferrer" className="inline-block">
              <img
                src={`https://img.youtube.com/vi/${vid}/hqdefault.jpg`}
                alt="Video del vehículo"
                className="w-72 max-w-full rounded-lg border border-brand-surface-2"
              />
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteActa, downloadDocumentoFirma, listActas } from "@/services/actas";
import EditarActaModal from "@/pages/EditarActaModal";
import RecepcionarModal from "@/pages/RecepcionarModal";
import { CerrarSinVentaModal, RegistrarVentaModal } from "@/pages/ActaModals";
import type { Acta } from "@/types";

const ESTADO_STYLES: Record<string, string> = {
  CAPTADO: "bg-sky-100 text-sky-700",
  RECEPCIONADO: "bg-blue-100 text-blue-700",
  CONTRATO_ACEPTADO: "bg-amber-100 text-amber-700",
  PUBLICADO: "bg-green-100 text-green-700",
  VENDIDO: "bg-purple-100 text-purple-700",
  PROSPECTO: "bg-gray-100 text-gray-600",
};

// Vendible/imprimible desde RECEPCIONADO (el auto ya llegó y el contrato está firmado).
const VENDIBLE = new Set(["RECEPCIONADO", "CONTRATO_ACEPTADO", "PUBLICADO"]);
const DOC_FIRMA = new Set(["RECEPCIONADO", "CONTRATO_ACEPTADO", "PUBLICADO", "VENDIDO"]);

export default function MisCaptaciones() {
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["actas", "mine"],
    queryFn: () => listActas({ mine: true }),
  });

  const [ventaFor, setVentaFor] = useState<Acta | null>(null);
  const [editFor, setEditFor] = useState<Acta | null>(null);
  const [cerrarFor, setCerrarFor] = useState<Acta | null>(null);
  const [recepcionarFor, setRecepcionarFor] = useState<Acta | null>(null);
  const invalidate = () => qc.invalidateQueries({ queryKey: ["actas"] });

  const eliminarMut = useMutation({
    mutationFn: (a: Acta) => deleteActa(a.id),
    onSuccess: invalidate,
    onError: (e: unknown) => alert(extractError(e)),
  });

  const documentoMut = useMutation({
    mutationFn: async (a: Acta) => {
      const blob = await downloadDocumentoFirma(a.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
    },
    onError: (e: unknown) => alert(extractError(e)),
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">Mis Captaciones</h1>
          <p className="text-sm text-brand-muted">Actas que has levantado</p>
        </div>
        <Link
          to="/actas/nueva"
          className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600"
        >
          + Nueva Acta de Recepción
        </Link>
      </div>

      {isLoading && <p className="text-brand-muted">Cargando…</p>}
      {isError && <p className="text-red-600">No se pudieron cargar tus captaciones.</p>}

      {data && data.length === 0 && (
        <div className="rounded-xl border border-dashed border-brand-surface-2 bg-white p-10 text-center">
          <p className="text-brand-muted">Aún no tienes actas levantadas.</p>
          <Link to="/actas/nueva" className="mt-2 inline-block font-medium text-brand-accent-600 hover:underline">
            Levanta tu primera acta →
          </Link>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-brand-surface-2 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-4 py-3 font-medium">PPU</th>
                <th className="px-4 py-3 font-medium">Vehículo</th>
                <th className="px-4 py-3 font-medium">Cliente</th>
                <th className="px-4 py-3 font-medium">Vendedor</th>
                <th className="px-4 py-3 font-medium">Precio</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-4 py-3 font-mono font-medium text-brand-ink">{a.ppu}</td>
                  <td className="px-4 py-3">
                    {a.vehiculo.marca} {a.vehiculo.modelo} <span className="text-brand-muted">{a.vehiculo.anio}</span>
                    {a.derivado && (
                      <span className="ml-2 rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700">
                        Derivado → {a.sucursal_venta}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-brand-muted">{a.cliente}</td>
                  <td className="px-4 py-3">{a.vendedor ?? <span className="text-brand-muted-2">—</span>}</td>
                  <td className="px-4 py-3">
                    ${(a.precio_venta_final ?? a.precio_venta_pactado).toLocaleString("es-CL")}
                    {a.precio_venta_final != null && <span className="ml-1 text-xs text-brand-muted-2">(final)</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_STYLES[a.estado_code] ?? "bg-gray-100 text-gray-600"}`}>
                      {a.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2 text-xs">
                      <Link to={`/actas/${a.id}`} className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface">
                        Ver
                      </Link>
                      {/* Si la venta se derivó a otra sucursal, la gestión (recepcionar,
                          vender, cerrar) es de esa sucursal; aquí el captador solo monitorea. */}
                      {a.derivado ? (
                        <span className="rounded bg-orange-50 px-2 py-1 text-orange-700">
                          Gestión en {a.sucursal_venta}
                        </span>
                      ) : (
                        <>
                          {a.estado_code === "CAPTADO" && !a.cerrada && (
                            <button
                              onClick={() => setRecepcionarFor(a)}
                              className="rounded bg-brand-accent px-2 py-1 font-medium text-black hover:bg-brand-accent-600"
                            >
                              Recepcionar
                            </button>
                          )}
                          {(a.estado_code === "CAPTADO" || a.estado_code === "RECEPCIONADO") && !a.cerrada && (
                            <>
                              <button
                                onClick={() => setEditFor(a)}
                                disabled={eliminarMut.isPending}
                                className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                              >
                                Editar
                              </button>
                              <button
                                onClick={() => setCerrarFor(a)}
                                className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface"
                              >
                                Cerrar sin venta
                              </button>
                              <button
                                onClick={() => {
                                  if (window.confirm(`¿Eliminar acta ${a.ppu}? Esta acción no se puede deshacer.`)) {
                                    eliminarMut.mutate(a);
                                  }
                                }}
                                disabled={eliminarMut.isPending}
                                className="rounded border border-red-200 px-2 py-1 text-red-700 hover:bg-red-50 disabled:opacity-60"
                              >
                                Eliminar
                              </button>
                            </>
                          )}
                          {VENDIBLE.has(a.estado_code) && !a.cerrada && (
                            <button
                              onClick={() => setVentaFor(a)}
                              className="rounded bg-brand-accent px-2 py-1 font-medium text-black hover:bg-brand-accent-600"
                            >
                              Registrar venta
                            </button>
                          )}
                          {DOC_FIRMA.has(a.estado_code) && (
                            <button
                              onClick={() => documentoMut.mutate(a)}
                              disabled={documentoMut.isPending}
                              className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                            >
                              PDF firma
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {ventaFor && (
        <RegistrarVentaModal acta={ventaFor} onClose={() => setVentaFor(null)} onDone={() => { setVentaFor(null); invalidate(); }} />
      )}
      {editFor && (
        <EditarActaModal actaId={editFor.id} onClose={() => setEditFor(null)} onDone={() => { setEditFor(null); invalidate(); }} />
      )}
      {cerrarFor && (
        <CerrarSinVentaModal acta={cerrarFor} onClose={() => setCerrarFor(null)} onDone={() => { setCerrarFor(null); invalidate(); }} />
      )}
      {recepcionarFor && (
        <RecepcionarModal acta={recepcionarFor} onClose={() => setRecepcionarFor(null)} onDone={() => { setRecepcionarFor(null); invalidate(); }} />
      )}
    </div>
  );
}


function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo completar la acción.";
}

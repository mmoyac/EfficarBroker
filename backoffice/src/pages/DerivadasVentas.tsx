import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { downloadDocumentoFirma, listActas } from "@/services/actas";
import RecepcionarModal from "@/pages/RecepcionarModal";
import { CerrarSinVentaModal, RegistrarVentaModal } from "@/pages/ActaModals";
import type { Acta } from "@/types";

const ESTADO_STYLES: Record<string, string> = {
  CAPTADO: "bg-sky-100 text-sky-700",
  RECEPCIONADO: "bg-blue-100 text-blue-700",
  CONTRATO_ACEPTADO: "bg-amber-100 text-amber-700",
  PUBLICADO: "bg-green-100 text-green-700",
  VENDIDO: "bg-purple-100 text-purple-700",
};

const VENDIBLE = new Set(["RECEPCIONADO", "CONTRATO_ACEPTADO", "PUBLICADO"]);
const DOC_FIRMA = new Set(["RECEPCIONADO", "CONTRATO_ACEPTADO", "PUBLICADO", "VENDIDO"]);

export default function DerivadasVentas() {
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["actas", "derivadas"],
    queryFn: () => listActas({ derivadas: true }),
  });

  const [ventaFor, setVentaFor] = useState<Acta | null>(null);
  const [recepcionarFor, setRecepcionarFor] = useState<Acta | null>(null);
  const [cerrarFor, setCerrarFor] = useState<Acta | null>(null);
  const invalidate = () => qc.invalidateQueries({ queryKey: ["actas"] });

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
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-brand-ink">Ventas Derivadas a mi Sucursal</h1>
        <p className="text-sm text-brand-muted">
          Autos captados en otra sucursal cuya venta se gestiona en la tuya. El auto llega acá: recepciónalo y véndelo.
        </p>
      </div>

      {isLoading && <p className="text-brand-muted">Cargando…</p>}
      {isError && <p className="text-red-600">No se pudieron cargar las ventas derivadas.</p>}

      {data && data.length === 0 && (
        <div className="rounded-xl border border-dashed border-brand-surface-2 bg-white p-10 text-center">
          <p className="text-brand-muted">No hay ventas derivadas a tu sucursal por ahora.</p>
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
                <th className="px-4 py-3 font-medium">Origen → Venta</th>
                <th className="px-4 py-3 font-medium">Captador</th>
                <th className="px-4 py-3 font-medium">Precio</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-4 py-3 font-mono font-medium text-brand-ink">{a.ppu}</td>
                  <td className="px-4 py-3">{a.vehiculo.marca} {a.vehiculo.modelo} <span className="text-brand-muted">{a.vehiculo.anio}</span></td>
                  <td className="px-4 py-3 text-brand-muted">{a.cliente}</td>
                  <td className="px-4 py-3 text-xs">
                    {a.sucursal} <span className="text-brand-muted-2">→</span>{" "}
                    <span className="font-medium text-orange-700">{a.sucursal_venta}</span>
                  </td>
                  <td className="px-4 py-3">{a.captador}</td>
                  <td className="px-4 py-3">${(a.precio_venta_final ?? a.precio_venta_pactado).toLocaleString("es-CL")}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_STYLES[a.estado_code] ?? "bg-gray-100 text-gray-600"}`}>
                      {a.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2 text-xs">
                      <Link to={`/actas/${a.id}`} className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface">Ver</Link>
                      {a.estado_code === "CAPTADO" && (
                        <button onClick={() => setRecepcionarFor(a)} className="rounded bg-brand-accent px-2 py-1 font-medium text-black hover:bg-brand-accent-600">
                          Recepcionar
                        </button>
                      )}
                      {VENDIBLE.has(a.estado_code) && !a.cerrada && (
                        <button onClick={() => setVentaFor(a)} className="rounded bg-brand-accent px-2 py-1 font-medium text-black hover:bg-brand-accent-600">
                          Registrar venta
                        </button>
                      )}
                      {DOC_FIRMA.has(a.estado_code) && (
                        <button onClick={() => documentoMut.mutate(a)} disabled={documentoMut.isPending} className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60">
                          PDF firma
                        </button>
                      )}
                      {(a.estado_code === "CAPTADO" || a.estado_code === "RECEPCIONADO") && !a.cerrada && (
                        <button onClick={() => setCerrarFor(a)} className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface">
                          Cerrar sin venta
                        </button>
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
      {recepcionarFor && (
        <RecepcionarModal acta={recepcionarFor} onClose={() => setRecepcionarFor(null)} onDone={() => { setRecepcionarFor(null); invalidate(); }} />
      )}
      {cerrarFor && (
        <CerrarSinVentaModal acta={cerrarFor} onClose={() => setCerrarFor(null)} onDone={() => { setCerrarFor(null); invalidate(); }} />
      )}
    </div>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo completar la acción.";
}

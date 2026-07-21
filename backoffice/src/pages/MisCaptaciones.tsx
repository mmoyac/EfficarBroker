import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  aceptarTerminos,
  cerrarSinVenta,
  deleteActa,
  downloadDocumentoFirma,
  listActas,
  registrarVenta,
} from "@/services/actas";
import { listEquipoVentas } from "@/services/vehiculos";
import { listMotivosCierre } from "@/services/catalogos";
import EditarActaModal from "@/pages/EditarActaModal";
import type { Acta } from "@/types";

const ESTADO_STYLES: Record<string, string> = {
  RECEPCIONADO: "bg-blue-100 text-blue-700",
  CONTRATO_ACEPTADO: "bg-amber-100 text-amber-700",
  PUBLICADO: "bg-green-100 text-green-700",
  VENDIDO: "bg-purple-100 text-purple-700",
  PROSPECTO: "bg-gray-100 text-gray-600",
};

const VENDIBLE = new Set(["CONTRATO_ACEPTADO", "PUBLICADO"]);
const DOC_FIRMA = new Set(["CONTRATO_ACEPTADO", "PUBLICADO", "VENDIDO"]);

export default function MisCaptaciones() {
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["actas", "mine"],
    queryFn: () => listActas({ mine: true }),
  });

  const [ventaFor, setVentaFor] = useState<Acta | null>(null);
  const [editFor, setEditFor] = useState<Acta | null>(null);
  const [cerrarFor, setCerrarFor] = useState<Acta | null>(null);
  const invalidate = () => qc.invalidateQueries({ queryKey: ["actas"] });

  const aceptarMut = useMutation({
    mutationFn: (a: Acta) => aceptarTerminos(a.id),
    onSuccess: invalidate,
    onError: (e: unknown) => alert(extractError(e)),
  });

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
                      {a.estado_code === "RECEPCIONADO" && !a.cerrada && (
                        <>
                          <button
                            onClick={() => setEditFor(a)}
                            disabled={aceptarMut.isPending || eliminarMut.isPending}
                            className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => aceptarMut.mutate(a)}
                            disabled={aceptarMut.isPending || eliminarMut.isPending}
                            className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                          >
                            Aceptar términos
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
                            disabled={aceptarMut.isPending || eliminarMut.isPending}
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
    </div>
  );
}

function RegistrarVentaModal({ acta, onClose, onDone }: { acta: Acta; onClose: () => void; onDone: () => void }) {
  const equipoQ = useQuery({ queryKey: ["equipo-ventas"], queryFn: () => listEquipoVentas() });
  const [vendedorId, setVendedorId] = useState<number | "">("");
  const [precio, setPrecio] = useState(String(acta.precio_venta_pactado));
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: () => registrarVenta(acta.id, Number(vendedorId), Number(precio || 0)),
    onSuccess: onDone,
    onError: (e: unknown) => setError(extractError(e)),
  });

  const comisionNeta = Math.max(acta.comision - acta.exclusividad_abono, 0);

  return (
    <Modal title="Registrar venta" onClose={onClose}>
      <p className="mb-4 text-sm text-brand-muted">
        {acta.ppu} · {acta.vehiculo.marca} {acta.vehiculo.modelo} · captó {acta.captador}
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          if (vendedorId === "") { setError("Selecciona al vendedor."); return; }
          mut.mutate();
        }}
        className="space-y-3"
      >
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-brand-ink">Vendedor (cierra la venta)</span>
          <select value={vendedorId} onChange={(e) => setVendedorId(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls} required>
            <option value="" disabled>Seleccionar ejecutivo</option>
            {equipoQ.data?.map((u) => (<option key={u.id} value={u.id}>{u.nombre}</option>))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-brand-ink">Precio de venta final (CLP)</span>
          <input type="number" value={precio} onChange={(e) => setPrecio(e.target.value)} className={inputCls} required />
        </label>

        <div className="rounded-lg bg-brand-surface p-3 text-sm">
          <div className="flex justify-between"><span>Comisión pactada</span><strong>${acta.comision.toLocaleString("es-CL")}</strong></div>
          <div className="flex justify-between text-brand-muted"><span>Abono ya adelantado</span><span>− ${acta.exclusividad_abono.toLocaleString("es-CL")}</span></div>
          <div className="mt-1 flex justify-between border-t border-brand-surface-2 pt-1">
            <span>Comisión a cobrar al cierre</span><strong className="text-brand-ink">${comisionNeta.toLocaleString("es-CL")}</strong>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">Cancelar</button>
          <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
            {mut.isPending ? "Registrando…" : "Confirmar venta"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function CerrarSinVentaModal({ acta, onClose, onDone }: { acta: Acta; onClose: () => void; onDone: () => void }) {
  const motivosQ = useQuery({ queryKey: ["motivos-cierre"], queryFn: listMotivosCierre });
  const [motivoId, setMotivoId] = useState<number | "">("");
  const [obs, setObs] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: () => cerrarSinVenta(acta.id, Number(motivoId), obs.trim() || null),
    onSuccess: onDone,
    onError: (e: unknown) => setError(extractError(e)),
  });

  return (
    <Modal title="Cerrar acta sin venta" onClose={onClose}>
      <p className="mb-4 text-sm text-brand-muted">
        {acta.ppu} · el abono de exclusividad quedará retenido como ingreso por gestión.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          if (motivoId === "") { setError("Selecciona el motivo."); return; }
          mut.mutate();
        }}
        className="space-y-3"
      >
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-brand-ink">Motivo</span>
          <select value={motivoId} onChange={(e) => setMotivoId(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls} required>
            <option value="" disabled>Seleccionar</option>
            {motivosQ.data?.map((m) => (<option key={m.id} value={m.id}>{m.nombre}</option>))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-brand-ink">Observación (opcional)</span>
          <input value={obs} onChange={(e) => setObs(e.target.value)} className={inputCls} />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">Cancelar</button>
          <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-ink px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-60">
            {mut.isPending ? "Cerrando…" : "Cerrar acta"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-brand-ink">{title}</h2>
        {children}
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo completar la acción.";
}

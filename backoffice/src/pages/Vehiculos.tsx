import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getVehiculoActas,
  listColores,
  listVehiculos,
  updateVehiculo,
} from "@/services/vehiculos";
import type { VehiculoFicha } from "@/types";

const fmt = (d: string) => new Date(d + "T00:00:00").toLocaleDateString("es-CL");

export default function Vehiculos() {
  const [q, setQ] = useState("");
  const [buscar, setBuscar] = useState("");
  const [editFor, setEditFor] = useState<VehiculoFicha | null>(null);
  const [detalleFor, setDetalleFor] = useState<VehiculoFicha | null>(null);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["vehiculos-ficha", buscar],
    queryFn: () => listVehiculos(buscar || undefined),
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-brand-ink">Vehículos</h1>
        <p className="text-sm text-brand-muted">
          Fichas físicas del tenant. Corregir un dato con actas firmadas afecta documentos ya emitidos.
        </p>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); setBuscar(q.trim()); }}
        className="mb-4 flex gap-2"
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar por PPU…"
          className="w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent sm:w-64"
        />
        <button type="submit" className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600">
          Buscar
        </button>
      </form>

      {isLoading && <p className="text-brand-muted">Cargando…</p>}

      {data && data.length === 0 && (
        <p className="rounded-xl border border-dashed border-brand-surface-2 bg-white p-10 text-center text-brand-muted">
          Sin vehículos para ese criterio.
        </p>
      )}

      {/* Escritorio: tabla. Móvil: tarjetas apiladas (mejor lectura en 5"). */}
      {data && data.length > 0 && (
        <div className="hidden overflow-x-auto rounded-xl border border-brand-surface-2 bg-white md:block">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-4 py-3 font-medium">PPU</th>
                <th className="px-4 py-3 font-medium">Marca / Modelo</th>
                <th className="px-4 py-3 font-medium">Año</th>
                <th className="px-4 py-3 font-medium">Motor / Chasis</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.map((v) => (
                <tr key={v.id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-4 py-3 font-mono font-medium text-brand-ink">{v.ppu}</td>
                  <td className="px-4 py-3">{v.marca} {v.modelo} <span className="text-brand-muted">{v.version}</span></td>
                  <td className="px-4 py-3">{v.anio}</td>
                  <td className="px-4 py-3 text-xs text-brand-muted">{v.n_motor ?? "—"} / {v.n_chasis ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2 text-xs">
                      <button onClick={() => setDetalleFor(v)} className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface">
                        Historial
                      </button>
                      <button onClick={() => setEditFor(v)} className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface">
                        Editar ficha
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.length > 0 && (
        <ul className="space-y-3 md:hidden">
          {data.map((v) => (
            <li key={v.id} className="rounded-xl border border-brand-surface-2 bg-white p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-mono font-semibold text-brand-ink">{v.ppu}</p>
                  <p className="truncate text-sm">
                    {v.marca} {v.modelo} <span className="text-brand-muted">{v.version}</span>
                  </p>
                </div>
                <span className="shrink-0 text-sm text-brand-muted">{v.anio}</span>
              </div>
              <p className="mt-2 text-xs text-brand-muted">
                Motor {v.n_motor ?? "—"} · Chasis {v.n_chasis ?? "—"}
              </p>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => setDetalleFor(v)}
                  className="flex-1 rounded-lg border border-brand-surface-2 px-3 py-2 text-sm hover:bg-brand-surface"
                >
                  Historial
                </button>
                <button
                  onClick={() => setEditFor(v)}
                  className="flex-1 rounded-lg border border-brand-surface-2 px-3 py-2 text-sm hover:bg-brand-surface"
                >
                  Editar ficha
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {editFor && (
        <EditarFichaModal
          ficha={editFor}
          onClose={() => setEditFor(null)}
          onDone={() => { setEditFor(null); qc.invalidateQueries({ queryKey: ["vehiculos-ficha"] }); }}
        />
      )}
      {detalleFor && (
        <HistorialModal ficha={detalleFor} onClose={() => setDetalleFor(null)} />
      )}
    </div>
  );
}

function EditarFichaModal({ ficha, onClose, onDone }: { ficha: VehiculoFicha; onClose: () => void; onDone: () => void }) {
  const coloresQ = useQuery({ queryKey: ["colores"], queryFn: listColores });
  // ¿Tiene actas firmadas? Consultamos el historial: si hay alguna cerrada o
  // con estado firmado, la edición exige motivo (afecta documentos emitidos).
  const historialQ = useQuery({ queryKey: ["vehiculo-actas", ficha.id], queryFn: () => getVehiculoActas(ficha.id) });
  const conHistorial = (historialQ.data ?? []).some(
    (h) => h.cerrada || ["CONTRATO_ACEPTADO", "PUBLICADO", "VENDIDO"].includes(h.estado_code),
  );

  const [ppu, setPpu] = useState(ficha.ppu);
  const [anio, setAnio] = useState(String(ficha.anio));
  const [nMotor, setNMotor] = useState(ficha.n_motor ?? "");
  const [nChasis, setNChasis] = useState(ficha.n_chasis ?? "");
  const [colorId, setColorId] = useState<number | "">(ficha.color_id ?? "");
  const [motivo, setMotivo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: () => updateVehiculo(ficha.id, {
      ppu: ppu.trim().toUpperCase(),
      anio: Number(anio),
      n_motor: nMotor.trim() || null,
      n_chasis: nChasis.trim() || null,
      color_id: colorId === "" ? null : Number(colorId),
      motivo: motivo.trim() || null,
    }),
    onSuccess: onDone,
    onError: (e: unknown) => setError(extractError(e)),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[90dvh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-brand-ink">Editar ficha · {ficha.ppu}</h2>
        {conHistorial && (
          <p className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">
            Este auto tiene actas firmadas. El cambio se propaga a documentos ya emitidos; indica un motivo.
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            if (conHistorial && !motivo.trim()) { setError("Indica el motivo del cambio."); return; }
            mut.mutate();
          }}
          className="mt-4 grid gap-3 sm:grid-cols-2"
        >
          <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">PPU</span><input value={ppu} onChange={(e) => setPpu(e.target.value)} className={inputCls} required /></label>
          <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Año</span><input type="number" value={anio} onChange={(e) => setAnio(e.target.value)} className={inputCls} required /></label>
          <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">N° Motor</span><input value={nMotor} onChange={(e) => setNMotor(e.target.value)} className={inputCls} /></label>
          <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">N° Chasis</span><input value={nChasis} onChange={(e) => setNChasis(e.target.value)} className={inputCls} /></label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Color</span>
            <select value={colorId} onChange={(e) => setColorId(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls}>
              <option value="">Seleccionar</option>
              {coloresQ.data?.map((c) => (<option key={c.id} value={c.id}>{c.nombre}</option>))}
            </select>
          </label>
          {conHistorial && (
            <label className="block sm:col-span-2">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Motivo del cambio</span>
              <input value={motivo} onChange={(e) => setMotivo(e.target.value)} className={inputCls} />
            </label>
          )}
          {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
          <div className="sm:col-span-2 mt-2 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">Cancelar</button>
            <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
              {mut.isPending ? "Guardando…" : "Guardar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function HistorialModal({ ficha, onClose }: { ficha: VehiculoFicha; onClose: () => void }) {
  const historialQ = useQuery({ queryKey: ["vehiculo-actas", ficha.id], queryFn: () => getVehiculoActas(ficha.id) });
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[90dvh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-brand-ink">Historial de recepciones · {ficha.ppu}</h2>
        <p className="mb-3 text-sm text-brand-muted">{ficha.marca} {ficha.modelo} {ficha.version}</p>
        {historialQ.isLoading && <p className="text-sm text-brand-muted">Cargando…</p>}
        {historialQ.data && historialQ.data.length === 0 && <p className="text-sm text-brand-muted">Sin actas.</p>}
        {historialQ.data && historialQ.data.length > 0 && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-2 py-2 font-medium">Recepción</th>
                <th className="px-2 py-2 font-medium">Dueño</th>
                <th className="px-2 py-2 font-medium">Captador</th>
                <th className="px-2 py-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {historialQ.data.map((h) => (
                <tr key={h.id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-2 py-2">{fmt(h.fecha_recepcion)}</td>
                  <td className="px-2 py-2">{h.cliente}</td>
                  <td className="px-2 py-2">{h.captador}</td>
                  <td className="px-2 py-2">{h.estado_code}{h.cerrada ? " (cerrada)" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="mt-4 flex justify-end">
          <button onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">Cerrar</button>
        </div>
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo guardar.";
}

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { recepcionar } from "@/services/actas";
import { listChecklistItems, listColores, listEstadosChecklist } from "@/services/vehiculos";
import type { Acta, ChecklistEntryInput } from "@/types";

type ChecklistState = Record<
  number,
  { presente: boolean; estado_checklist_id: number | ""; fecha_vencimiento: string; observacion: string }
>;

/** Recepción del auto: el cliente llegó a la sucursal. Aquí se registran los
 *  datos físicos (motor/chasis/km/color) y el checklist de 12 puntos, y el acta
 *  pasa de CAPTADO a RECEPCIONADO (contrato firmado). */
export default function RecepcionarModal({ acta, onClose, onDone }: {
  acta: Acta; onClose: () => void; onDone: () => void;
}) {
  const qc = useQueryClient();
  const itemsQ = useQuery({ queryKey: ["checklist-items"], queryFn: listChecklistItems });
  const coloresQ = useQuery({ queryKey: ["colores"], queryFn: listColores });
  const estadosQ = useQuery({ queryKey: ["estados-checklist"], queryFn: listEstadosChecklist });

  const [nMotor, setNMotor] = useState(acta.vehiculo.n_motor ?? "");
  const [nChasis, setNChasis] = useState(acta.vehiculo.n_chasis ?? "");
  const [km, setKm] = useState(acta.km_ingreso ? String(acta.km_ingreso) : "");
  const [colorId, setColorId] = useState<number | "">(acta.vehiculo.color_id ?? "");
  const [checklist, setChecklist] = useState<ChecklistState>({});
  const [error, setError] = useState<string | null>(null);

  const items = useMemo(() => (itemsQ.data ?? []).slice().sort((a, b) => a.orden - b.orden), [itemsQ.data]);
  const getRow = (id: number) => checklist[id] ?? { presente: false, estado_checklist_id: "" as number | "", fecha_vencimiento: "", observacion: "" };
  const setRow = (id: number, patch: Partial<ChecklistState[number]>) => setChecklist((c) => ({ ...c, [id]: { ...getRow(id), ...patch } }));

  const mut = useMutation({
    mutationFn: () => {
      const checklistPayload: ChecklistEntryInput[] = items.map((it) => {
        const r = getRow(it.id);
        return {
          checklist_item_id: it.id,
          presente: r.presente,
          estado_checklist_id: r.estado_checklist_id === "" ? null : Number(r.estado_checklist_id),
          fecha_vencimiento: r.fecha_vencimiento || null,
          observacion: r.observacion || null,
        };
      });
      return recepcionar(acta.id, {
        n_motor: nMotor.trim() || null,
        n_chasis: nChasis.trim() || null,
        color_id: colorId === "" ? null : Number(colorId),
        km_ingreso: Number(km || 0),
        checklist: checklistPayload,
      });
    },
    onSuccess: () => {
      qc.removeQueries({ queryKey: ["acta", acta.id] });
      qc.invalidateQueries({ queryKey: ["actas"] });
      onDone();
    },
    onError: (e: unknown) => setError(extractError(e)),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4" onClick={onClose}>
      <div className="my-6 w-full max-w-3xl rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-brand-ink">Recepcionar auto · {acta.ppu}</h2>
        <p className="mb-4 text-sm text-brand-muted">
          {acta.vehiculo.marca} {acta.vehiculo.modelo} · el auto llegó a la sucursal. Registra la inspección física y el checklist; el acta quedará RECEPCIONADA y con el contrato firmado.
        </p>
        <form
          onSubmit={(e) => { e.preventDefault(); setError(null); mut.mutate(); }}
          className="space-y-5"
        >
          <fieldset className="grid gap-3 sm:grid-cols-4">
            <legend className="mb-1 text-sm font-semibold text-brand-ink">Inspección física</legend>
            <Text label="N° Motor" value={nMotor} onChange={setNMotor} />
            <Text label="N° Chasis" value={nChasis} onChange={setNChasis} />
            <Text label="Kilometraje" type="number" value={km} onChange={setKm} />
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-brand-muted">Color</span>
              <select value={colorId} onChange={(e) => setColorId(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls}>
                <option value="">Seleccionar</option>
                {coloresQ.data?.map((c) => (<option key={c.id} value={c.id}>{c.nombre}</option>))}
              </select>
            </label>
          </fieldset>

          <div>
            <p className="mb-2 text-sm font-semibold text-brand-ink">Checklist de 12 puntos</p>
            <div className="space-y-2">
              {items.map((it) => {
                const r = getRow(it.id);
                return (
                  <div key={it.id} className="grid grid-cols-1 items-center gap-2 rounded-lg border border-brand-surface-2 p-2 sm:grid-cols-12">
                    <label className="flex items-center gap-2 sm:col-span-4">
                      <input type="checkbox" checked={r.presente} onChange={(e) => setRow(it.id, { presente: e.target.checked })} />
                      <span className="text-sm text-brand-ink">{it.nombre}</span>
                    </label>
                    <select value={r.estado_checklist_id} onChange={(e) => setRow(it.id, { estado_checklist_id: e.target.value === "" ? "" : Number(e.target.value) })} className={`${inputCls} sm:col-span-2`}>
                      <option value="">Estado…</option>
                      {estadosQ.data?.map((es) => (<option key={es.id} value={es.id}>{es.nombre}</option>))}
                    </select>
                    {it.requiere_vencimiento ? (
                      <label className="sm:col-span-3 flex flex-col">
                        <span className="text-[10px] uppercase text-brand-muted-2">Vence</span>
                        <input type="date" value={r.fecha_vencimiento} onChange={(e) => setRow(it.id, { fecha_vencimiento: e.target.value })} className={inputCls} />
                      </label>
                    ) : (<span className="sm:col-span-3" />)}
                    <input placeholder="Observación" value={r.observacion} onChange={(e) => setRow(it.id, { observacion: e.target.value })} className={`${inputCls} sm:col-span-3`} />
                  </div>
                );
              })}
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">Cancelar</button>
            <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
              {mut.isPending ? "Recepcionando…" : "Confirmar recepción"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function Text({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-brand-muted">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className={inputCls} />
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo recepcionar el auto.";
}

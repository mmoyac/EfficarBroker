import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { cerrarSinVenta, registrarVenta } from "@/services/actas";
import { listEquipoVentas } from "@/services/vehiculos";
import { listMotivosCierre } from "@/services/catalogos";
import type { Acta } from "@/types";

// Modales de acción sobre un acta, compartidos por "Mis Captaciones" y
// "Ventas Derivadas a mi Sucursal".

export function RegistrarVentaModal({ acta, onClose, onDone }: { acta: Acta; onClose: () => void; onDone: () => void }) {
  // Al vender un acta derivada, el vendedor debe pertenecer a la sucursal de
  // venta; filtramos el equipo por esa sucursal.
  const equipoQ = useQuery({
    queryKey: ["equipo-ventas", acta.sucursal_venta_id],
    queryFn: () => listEquipoVentas(acta.sucursal_venta_id),
  });
  const [vendedorId, setVendedorId] = useState<number | "">(acta.vendedor_user_id ?? "");
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
        {acta.derivado ? <> · venta en {acta.sucursal_venta}</> : null}
      </p>
      <form
        onSubmit={(e) => { e.preventDefault(); setError(null); if (vendedorId === "") { setError("Selecciona al vendedor."); return; } mut.mutate(); }}
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

export function CerrarSinVentaModal({ acta, onClose, onDone }: { acta: Acta; onClose: () => void; onDone: () => void }) {
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
        onSubmit={(e) => { e.preventDefault(); setError(null); if (motivoId === "") { setError("Selecciona el motivo."); return; } mut.mutate(); }}
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

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { crearOrdenPago, listComisiones, listOrdenesPago } from "@/services/comisiones";
import { listEquipoVentas } from "@/services/vehiculos";

const clp = (n: number) => `$${n.toLocaleString("es-CL")}`;
const fmt = (d: string) => new Date(d.slice(0, 10) + "T00:00:00").toLocaleDateString("es-CL");

// Generación de órdenes de pago (liquidación agrupada) — rol Management/TenantAdmin.
export default function OrdenesPago() {
  const qc = useQueryClient();
  const ordenesQ = useQuery({ queryKey: ["ordenes-pago", false], queryFn: () => listOrdenesPago({}) });
  const equipoQ = useQuery({ queryKey: ["equipo-ventas"], queryFn: () => listEquipoVentas() });
  // Vista de pendientes de todo el tenant, para saber a quién liquidar.
  const pendientesQ = useQuery({ queryKey: ["comisiones", false, "PENDIENTE"], queryFn: () => listComisiones({ mine: false, estado_pago: "PENDIENTE" }) });

  const [beneficiario, setBeneficiario] = useState<number | "">("");
  const hoy = new Date();
  const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1).toISOString().slice(0, 10);
  const ultimoDia = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0).toISOString().slice(0, 10);
  const [desde, setDesde] = useState(primerDia);
  const [hasta, setHasta] = useState(ultimoDia);
  const [fechaPago, setFechaPago] = useState(hoy.toISOString().slice(0, 10));
  const [base, setBase] = useState("0");
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: () => crearOrdenPago({
      beneficiario_user_id: Number(beneficiario),
      periodo_desde: desde, periodo_hasta: hasta, fecha_pago: fechaPago, monto_base: Number(base || 0),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ordenes-pago"] });
      qc.invalidateQueries({ queryKey: ["comisiones"] });
      setError(null);
    },
    onError: (e: unknown) => setError(extractError(e)),
  });

  // Pendiente por ejecutivo (para orientar la liquidación).
  const pendientePorUser: Record<string, number> = {};
  for (const c of pendientesQ.data?.items ?? []) {
    pendientePorUser[c.beneficiario] = (pendientePorUser[c.beneficiario] ?? 0) + c.monto;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-ink">Órdenes de Pago</h1>
        <p className="text-sm text-brand-muted">Liquida las comisiones de un ejecutivo agrupadas por período (mínimo + comisiones).</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <form
          onSubmit={(e) => { e.preventDefault(); setError(null); if (beneficiario === "") { setError("Selecciona el ejecutivo."); return; } mut.mutate(); }}
          className="space-y-4 rounded-xl border border-brand-surface-2 bg-white p-5 lg:col-span-1"
        >
          <h2 className="font-semibold text-brand-ink">Nueva orden</h2>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Ejecutivo</span>
            <select value={beneficiario} onChange={(e) => setBeneficiario(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls} required>
              <option value="">Seleccionar</option>
              {equipoQ.data?.map((u) => (
                <option key={u.id} value={u.id}>{u.nombre}{pendientePorUser[u.nombre] ? ` — pendiente ${clp(pendientePorUser[u.nombre])}` : ""}</option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block"><span className="mb-1 block text-xs font-medium text-brand-muted">Desde</span><input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} className={inputCls} /></label>
            <label className="block"><span className="mb-1 block text-xs font-medium text-brand-muted">Hasta</span><input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} className={inputCls} /></label>
          </div>
          <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Fecha de pago</span><input type="date" value={fechaPago} onChange={(e) => setFechaPago(e.target.value)} className={inputCls} /></label>
          <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Mínimo / base (CLP)</span><input type="number" value={base} onChange={(e) => setBase(e.target.value)} className={inputCls} /></label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={mut.isPending} className="w-full rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
            {mut.isPending ? "Generando…" : "Generar orden de pago"}
          </button>
          {mut.data && (
            <p className="text-sm text-green-700">
              Orden #{mut.data.id}: {clp(mut.data.monto_comisiones)} comisiones + {clp(mut.data.monto_base)} base = <strong>{clp(mut.data.monto_total)}</strong>
            </p>
          )}
        </form>

        <div className="rounded-xl border border-brand-surface-2 bg-white lg:col-span-2">
          <h2 className="border-b border-brand-surface-2 px-4 py-3 font-semibold text-brand-ink">Órdenes emitidas</h2>
          {ordenesQ.data && ordenesQ.data.length === 0 && <p className="p-6 text-center text-brand-muted">Aún no hay órdenes de pago.</p>}
          {ordenesQ.data && ordenesQ.data.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                    <th className="px-4 py-2 font-medium">Ejecutivo</th>
                    <th className="px-4 py-2 font-medium">Período</th>
                    <th className="px-4 py-2 font-medium">Pago</th>
                    <th className="px-4 py-2 font-medium">Comisiones</th>
                    <th className="px-4 py-2 font-medium">Base</th>
                    <th className="px-4 py-2 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {ordenesQ.data.map((o) => (
                    <tr key={o.id} className="border-b border-brand-surface-2 last:border-0">
                      <td className="px-4 py-2">{o.beneficiario}</td>
                      <td className="px-4 py-2 text-brand-muted">{fmt(o.periodo_desde)} – {fmt(o.periodo_hasta)}</td>
                      <td className="px-4 py-2">{fmt(o.fecha_pago)}</td>
                      <td className="px-4 py-2">{clp(o.monto_comisiones)}</td>
                      <td className="px-4 py-2">{clp(o.monto_base)}</td>
                      <td className="px-4 py-2 font-semibold">{clp(o.monto_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
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
  return "No se pudo generar la orden.";
}

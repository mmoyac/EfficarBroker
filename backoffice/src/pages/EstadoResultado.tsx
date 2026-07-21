import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getEstadoResultado } from "@/services/comisiones";

const clp = (n: number) => `$${n.toLocaleString("es-CL")}`;

// Estado de resultados del negocio para el administrador (rol TenantAdmin).
export default function EstadoResultado() {
  const hoy = new Date();
  const [desde, setDesde] = useState(new Date(hoy.getFullYear(), hoy.getMonth(), 1).toISOString().slice(0, 10));
  const [hasta, setHasta] = useState(new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0).toISOString().slice(0, 10));

  const q = useQuery({
    queryKey: ["estado-resultado", desde, hasta],
    queryFn: () => getEstadoResultado({ desde, hasta }),
  });
  const r = q.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">Estado de Resultados</h1>
          <p className="text-sm text-brand-muted">Desempeño del corretaje en el período seleccionado.</p>
        </div>
        <div className="flex items-end gap-2">
          <label className="block"><span className="mb-1 block text-xs font-medium text-brand-muted">Desde</span><input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} className={inputCls} /></label>
          <label className="block"><span className="mb-1 block text-xs font-medium text-brand-muted">Hasta</span><input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} className={inputCls} /></label>
        </div>
      </div>

      {q.isLoading && <p className="text-brand-muted">Cargando…</p>}
      {r && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Tile label="Autos vendidos" value={String(r.ventas_cantidad)} />
            <Tile label="Monto transado" value={clp(r.monto_transado)} />
            <Tile label="Comisión de la empresa" value={clp(r.comision_empresa)} sub="ingreso por corretaje" />
            <Tile label="Comisiones a ejecutivos" value={clp(r.comisiones_ejecutivos)} sub="egreso" accent="amber" />
          </div>

          <div className="rounded-xl border border-brand-surface-2 bg-white p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-brand-muted-2">Margen de corretaje</p>
                <p className="text-xs text-brand-muted-2">comisión de la empresa − comisiones a ejecutivos</p>
              </div>
              <p className="text-3xl font-bold text-brand-ink">{clp(r.margen_corretaje)}</p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Tile label="Abonos retenidos" value={clp(r.abonos_retenidos)} sub="ingreso por gestión (autos no vendidos)" accent="green" />
            <Tile label="Abonos comprometidos" value={clp(r.abonos_comprometidos)} sub="cobrados, aún no devengados" />
          </div>
        </>
      )}
    </div>
  );
}

function Tile({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: "amber" | "green" }) {
  const color = accent === "amber" ? "text-amber-700" : accent === "green" ? "text-green-700" : "text-brand-ink";
  return (
    <div className="rounded-xl border border-brand-surface-2 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-brand-muted-2">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-brand-muted-2">{sub}</p>}
    </div>
  );
}

const inputCls =
  "rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

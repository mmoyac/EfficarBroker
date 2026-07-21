import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listComisiones, listOrdenesPago } from "@/services/comisiones";
import { useAuth } from "@/context/AuthContext";

const clp = (n: number) => `$${n.toLocaleString("es-CL")}`;
const fmt = (d: string | null) => (d ? new Date(d.slice(0, 10) + "T00:00:00").toLocaleDateString("es-CL") : "—");

const TIPO_STYLES: Record<string, string> = {
  CAPTACION: "bg-sky-100 text-sky-700",
  VENTA: "bg-green-100 text-green-700",
};
const PAGO_STYLES: Record<string, string> = {
  PENDIENTE: "bg-amber-100 text-amber-700",
  PAGADA: "bg-purple-100 text-purple-700",
};

const TRANSVERSALES = new Set(["Management", "TenantAdmin", "SuperAdmin"]);

export default function Comisiones() {
  const { user } = useAuth();
  const esTransversal = TRANSVERSALES.has(user?.role_code ?? "");
  const [verTodas, setVerTodas] = useState(false);
  const [estado, setEstado] = useState("");
  const mine = !(esTransversal && verTodas);

  const comisionesQ = useQuery({
    queryKey: ["comisiones", mine, estado],
    queryFn: () => listComisiones({ mine, estado_pago: estado || undefined }),
  });
  const ordenesQ = useQuery({
    queryKey: ["ordenes-pago", mine],
    queryFn: () => listOrdenesPago({ mine }),
  });

  const data = comisionesQ.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">Mis Comisiones</h1>
          <p className="text-sm text-brand-muted">Incentivos por captación y venta{esTransversal && verTodas ? " · todo el tenant" : ""}</p>
        </div>
        <div className="flex items-center gap-3">
          {esTransversal && (
            <label className="flex items-center gap-2 text-sm text-brand-muted">
              <input type="checkbox" checked={verTodas} onChange={(e) => setVerTodas(e.target.checked)} />
              Ver todas del tenant
            </label>
          )}
          <select value={estado} onChange={(e) => setEstado(e.target.value)} className="rounded-lg border border-brand-surface-2 px-3 py-2 text-sm">
            <option value="">Todos los estados</option>
            <option value="PENDIENTE">Pendientes</option>
            <option value="PAGADA">Pagadas</option>
          </select>
        </div>
      </div>

      {data && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Tile label="Total" value={clp(data.total)} />
          <Tile label="Pendiente de pago" value={clp(data.total_pendiente)} accent="amber" />
          <Tile label="Pagado" value={clp(data.total_pagada)} accent="purple" />
        </div>
      )}

      <section className="rounded-xl border border-brand-surface-2 bg-white">
        <h2 className="border-b border-brand-surface-2 px-4 py-3 font-semibold text-brand-ink">Comisiones</h2>
        {comisionesQ.isLoading && <p className="p-4 text-brand-muted">Cargando…</p>}
        {data && data.items.length === 0 && <p className="p-6 text-center text-brand-muted">Aún no tienes comisiones.</p>}
        {data && data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                  <th className="px-4 py-2 font-medium">Tipo</th>
                  <th className="px-4 py-2 font-medium">PPU / Vehículo</th>
                  <th className="px-4 py-2 font-medium">Cliente</th>
                  {!mine && <th className="px-4 py-2 font-medium">Beneficiario</th>}
                  <th className="px-4 py-2 font-medium">Venta</th>
                  <th className="px-4 py-2 font-medium">Monto</th>
                  <th className="px-4 py-2 font-medium">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id} className="border-b border-brand-surface-2 last:border-0">
                    <td className="px-4 py-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${TIPO_STYLES[c.tipo_code] ?? "bg-gray-100"}`}>{c.tipo}</span>
                    </td>
                    <td className="px-4 py-2"><span className="font-mono">{c.ppu}</span> · {c.vehiculo}</td>
                    <td className="px-4 py-2 text-brand-muted">{c.cliente}</td>
                    {!mine && <td className="px-4 py-2">{c.beneficiario}</td>}
                    <td className="px-4 py-2 text-brand-muted">{fmt(c.fecha_venta)}</td>
                    <td className="px-4 py-2 font-medium">{clp(c.monto)}</td>
                    <td className="px-4 py-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${PAGO_STYLES[c.estado_pago_code] ?? "bg-gray-100"}`}>{c.estado_pago}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-brand-surface-2 bg-white">
        <h2 className="border-b border-brand-surface-2 px-4 py-3 font-semibold text-brand-ink">Órdenes de pago</h2>
        {ordenesQ.data && ordenesQ.data.length === 0 && <p className="p-6 text-center text-brand-muted">Aún no hay órdenes de pago.</p>}
        {ordenesQ.data && ordenesQ.data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                  {!mine && <th className="px-4 py-2 font-medium">Ejecutivo</th>}
                  <th className="px-4 py-2 font-medium">Período</th>
                  <th className="px-4 py-2 font-medium">Fecha de pago</th>
                  <th className="px-4 py-2 font-medium">Comisiones</th>
                  <th className="px-4 py-2 font-medium">Base (mínimo)</th>
                  <th className="px-4 py-2 font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {ordenesQ.data.map((o) => (
                  <tr key={o.id} className="border-b border-brand-surface-2 last:border-0">
                    {!mine && <td className="px-4 py-2">{o.beneficiario}</td>}
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
      </section>
    </div>
  );
}

function Tile({ label, value, accent }: { label: string; value: string; accent?: "amber" | "purple" }) {
  const ring = accent === "amber" ? "text-amber-700" : accent === "purple" ? "text-purple-700" : "text-brand-ink";
  return (
    <div className="rounded-xl border border-brand-surface-2 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-brand-muted-2">{label}</p>
      <p className={`text-2xl font-semibold ${ring}`}>{value}</p>
    </div>
  );
}

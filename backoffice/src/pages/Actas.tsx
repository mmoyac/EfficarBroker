import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listActas } from "@/services/actas";
import { useAuth } from "@/context/AuthContext";

const ESTADO_STYLES: Record<string, string> = {
  CAPTADO: "bg-sky-100 text-sky-700",
  RECEPCIONADO: "bg-blue-100 text-blue-700",
  CONTRATO_ACEPTADO: "bg-amber-100 text-amber-700",
  PUBLICADO: "bg-green-100 text-green-700",
  VENDIDO: "bg-purple-100 text-purple-700",
  PROSPECTO: "bg-gray-100 text-gray-600",
};

const TRANSVERSALES = new Set(["Management", "TenantAdmin", "SuperAdmin"]);

export default function Actas() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const esTransversal = TRANSVERSALES.has(user?.role_code ?? "");
  // Los roles transversales pueden ampliar el alcance a todo el tenant.
  const [verTodas, setVerTodas] = useState(false);
  const mine = !(esTransversal && verTodas);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["actas", mine ? "mine" : "all"],
    queryFn: () => listActas({ mine }),
  });

  const clp = (n: number) => `$${n.toLocaleString("es-CL")}`;
  const fmt = (d: string) => new Date(d + "T00:00:00").toLocaleDateString("es-CL");

  const rows = useMemo(() => data ?? [], [data]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">Actas de Recepción</h1>
          <p className="text-sm text-brand-muted">
            {mine ? "Tus recepciones" : "Todas las recepciones del tenant"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {esTransversal && (
            <label className="flex items-center gap-2 text-sm text-brand-muted">
              <input
                type="checkbox"
                checked={verTodas}
                onChange={(e) => setVerTodas(e.target.checked)}
              />
              Ver todas del tenant
            </label>
          )}
          <Link
            to="/actas/nueva"
            className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600"
          >
            + Nueva acta
          </Link>
        </div>
      </div>

      {isLoading && <p className="text-brand-muted">Cargando…</p>}
      {isError && <p className="text-red-600">No se pudieron cargar las actas.</p>}

      {data && rows.length === 0 && (
        <div className="rounded-xl border border-dashed border-brand-surface-2 bg-white p-10 text-center">
          <p className="text-brand-muted">Aún no hay actas de recepción.</p>
          <Link to="/actas/nueva" className="mt-2 inline-block font-medium text-brand-accent-600 hover:underline">
            Levanta tu primera acta →
          </Link>
        </div>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-brand-surface-2 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-4 py-3 font-medium">PPU</th>
                <th className="px-4 py-3 font-medium">Vehículo</th>
                <th className="px-4 py-3 font-medium">Cliente</th>
                {!mine && <th className="px-4 py-3 font-medium">Captador</th>}
                <th className="px-4 py-3 font-medium">Recepción</th>
                <th className="px-4 py-3 font-medium">Precio pactado</th>
                <th className="px-4 py-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr
                  key={a.id}
                  onClick={() => navigate(`/actas/${a.id}`)}
                  className="cursor-pointer border-b border-brand-surface-2 last:border-0 hover:bg-brand-surface/60"
                >
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
                  {!mine && <td className="px-4 py-3">{a.captador}</td>}
                  <td className="px-4 py-3 text-brand-muted">{fmt(a.fecha_recepcion)}</td>
                  <td className="px-4 py-3">{clp(a.precio_venta_pactado)}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_STYLES[a.estado_code] ?? "bg-gray-100 text-gray-600"}`}>
                      {a.estado}
                    </span>
                    {a.cerrada && a.estado_code !== "VENDIDO" && (
                      <span className="ml-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">cerrada</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

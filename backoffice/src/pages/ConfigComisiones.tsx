import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getParametros, updateParametros } from "@/services/comisiones";

// Parámetros de la comisión del ejecutivo (rol TenantAdmin).
export default function ConfigComisiones() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["parametros-comision"], queryFn: getParametros });

  const [pool, setPool] = useState("");
  const [capt, setCapt] = useState("");
  const [venta, setVenta] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState(false);

  useEffect(() => {
    if (q.data) {
      setPool(String(q.data.pool_pct));
      setCapt(String(q.data.captacion_pct));
      setVenta(String(q.data.venta_pct));
    }
  }, [q.data]);

  const mut = useMutation({
    mutationFn: () => updateParametros({ pool_pct: Number(pool), captacion_pct: Number(capt), venta_pct: Number(venta) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["parametros-comision"] }); setOkMsg(true); setError(null); },
    onError: (e: unknown) => { setOkMsg(false); setError(extractError(e)); },
  });

  const suma = Number(capt || 0) + Number(venta || 0);

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold text-brand-ink">Parámetros de Comisión</h1>
      <p className="mb-6 text-sm text-brand-muted">
        Define cuánto de la comisión de la empresa gana el equipo de ventas y cómo se reparte entre captación y venta.
      </p>

      <form
        onSubmit={(e) => { e.preventDefault(); setError(null); if (suma !== 100) { setError("Captación + venta debe sumar 100."); return; } mut.mutate(); }}
        className="space-y-5 rounded-xl border border-brand-surface-2 bg-white p-6"
      >
        <Field label="Pool de ejecutivos (% de la comisión de la empresa)" value={pool} onChange={setPool}
          hint="Ej: 20 → el 20% de lo que cobra la empresa se reparte entre captador y vendedor." />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Captación (%)" value={capt} onChange={setCapt} />
          <Field label="Venta (%)" value={venta} onChange={setVenta} />
        </div>
        <p className={`text-xs ${suma === 100 ? "text-brand-muted-2" : "text-red-600"}`}>
          Captación + venta = {suma}% {suma === 100 ? "✓" : "(debe sumar 100)"}
        </p>

        <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
          Los cambios rigen para las ventas futuras. Las comisiones ya generadas conservan su monto.
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {okMsg && <p className="text-sm text-green-700">Parámetros guardados.</p>}

        <div className="flex justify-end">
          <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-5 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
            {mut.isPending ? "Guardando…" : "Guardar parámetros"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, hint }: { label: string; value: string; onChange: (v: string) => void; hint?: string }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-brand-ink">{label}</span>
      <input type="number" value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40" required />
      {hint && <span className="mt-1 block text-xs text-brand-muted-2">{hint}</span>}
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudieron guardar los parámetros.";
}

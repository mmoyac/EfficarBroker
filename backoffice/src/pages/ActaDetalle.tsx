import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getActa } from "@/services/actas";
import { getVehiculoActas } from "@/services/vehiculos";

const clp = (n: number | null | undefined) => `$${(n ?? 0).toLocaleString("es-CL")}`;
const fmt = (d: string | null) => (d ? new Date(d + "T00:00:00").toLocaleDateString("es-CL") : "—");

export default function ActaDetalle() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const actaId = Number(id);

  const actaQ = useQuery({ queryKey: ["acta", actaId], queryFn: () => getActa(actaId) });
  const historialQ = useQuery({
    queryKey: ["vehiculo-actas", actaQ.data?.vehiculo_id],
    queryFn: () => getVehiculoActas(actaQ.data!.vehiculo_id),
    enabled: actaQ.data != null,
  });

  if (actaQ.isLoading) return <p className="text-brand-muted">Cargando…</p>;
  if (actaQ.isError || !actaQ.data) return <p className="text-red-600">No se pudo cargar el acta.</p>;

  const a = actaQ.data;
  const v = a.vehiculo;
  const anteriores = (historialQ.data ?? []).filter((h) => h.id !== a.id);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <button onClick={() => navigate("/actas")} className="text-sm text-brand-muted hover:underline">
        ← Volver a actas
      </button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">
            {v.marca} {v.modelo} <span className="font-mono text-brand-muted">{a.ppu}</span>
          </h1>
          <p className="text-sm text-brand-muted">
            {a.estado} · recepción {fmt(a.fecha_recepcion)} · captó {a.captador}
          </p>
        </div>
      </div>

      <Section title="Vehículo">
        <Grid>
          <Field label="Marca / Modelo" value={`${v.marca} ${v.modelo}`} />
          <Field label="Versión" value={v.version} />
          <Field label="Año" value={String(v.anio)} />
          <Field label="Color" value={v.color ?? "—"} />
          <Field label="N° Motor" value={v.n_motor ?? "—"} />
          <Field label="N° Chasis" value={v.n_chasis ?? "—"} />
          <Field label="Kilometraje (esta recepción)" value={a.km_ingreso.toLocaleString("es-CL")} />
        </Grid>
      </Section>

      <Section title="Cliente (dueño en esta recepción)">
        <Grid>
          <Field label="Nombre" value={a.cliente_detalle.nombre} />
          <Field label="RUT" value={a.cliente_detalle.rut} />
          <Field label="Email" value={a.cliente_detalle.email ?? "—"} />
          <Field label="Teléfono" value={a.cliente_detalle.telefono ?? "—"} />
          <Field label="Domicilio" value={a.cliente_detalle.domicilio ?? "—"} />
          <Field label="Comuna" value={a.cliente_detalle.comuna ?? "—"} />
        </Grid>
      </Section>

      <Section title="Orden de venta">
        <Grid>
          <Field label="Precio pactado" value={clp(a.precio_venta_pactado)} />
          <Field label="Tipo de comisión" value={a.tipo_comision ?? "—"} />
          <Field label="Comisión" value={clp(a.comision)} />
          <Field label="Abono exclusividad" value={clp(a.exclusividad_abono)} />
          <Field label="Comisión a cobrar al cierre" value={clp(a.comision_neta)} hint="ya descontado el abono" />
          <Field label="Estado del abono" value={a.estado_abono} />
          <Field label="Vigencia" value={`${a.vigencia_dias} días`} />
          <Field label="Sucursal de venta" value={a.sucursal_venta + (a.derivado ? " (derivada)" : "")} />
        </Grid>
      </Section>

      <Section title="Checklist de recepción">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-3 py-2 font-medium">Punto</th>
                <th className="px-3 py-2 font-medium">Presente</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2 font-medium">Vencimiento</th>
                <th className="px-3 py-2 font-medium">Observación</th>
              </tr>
            </thead>
            <tbody>
              {a.checklist.map((c) => (
                <tr key={c.checklist_item_id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-3 py-2">{c.item}</td>
                  <td className="px-3 py-2">{c.presente ? "Sí" : "No"}</td>
                  <td className="px-3 py-2">{c.estado ?? "—"}</td>
                  <td className="px-3 py-2">{fmt(c.fecha_vencimiento)}</td>
                  <td className="px-3 py-2 text-brand-muted">{c.observacion ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Historial de recepciones de este vehículo">
        {anteriores.length === 0 ? (
          <p className="text-sm text-brand-muted">Es la primera vez que este auto se corretó en el tenant.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                  <th className="px-3 py-2 font-medium">Recepción</th>
                  <th className="px-3 py-2 font-medium">Dueño</th>
                  <th className="px-3 py-2 font-medium">Captador</th>
                  <th className="px-3 py-2 font-medium">Estado</th>
                  <th className="px-3 py-2 font-medium">Venta</th>
                </tr>
              </thead>
              <tbody>
                {anteriores.map((h) => (
                  <tr
                    key={h.id}
                    onClick={() => navigate(`/actas/${h.id}`)}
                    className="cursor-pointer border-b border-brand-surface-2 last:border-0 hover:bg-brand-surface/60"
                  >
                    <td className="px-3 py-2">{fmt(h.fecha_recepcion)}</td>
                    <td className="px-3 py-2">{h.cliente}</td>
                    <td className="px-3 py-2">{h.captador}</td>
                    <td className="px-3 py-2">{h.estado_code}{h.cerrada ? " (cerrada)" : ""}</td>
                    <td className="px-3 py-2">
                      {h.precio_venta_final != null ? `${clp(h.precio_venta_final)} · ${fmt(h.fecha_venta)}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-brand-surface-2 bg-white p-5">
      <h2 className="mb-4 font-semibold text-brand-ink">{title}</h2>
      {children}
    </section>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{children}</div>;
}

function Field({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-brand-muted-2">{label}</p>
      <p className="text-sm text-brand-ink">{value}</p>
      {hint && <p className="text-xs text-brand-muted-2">{hint}</p>}
    </div>
  );
}

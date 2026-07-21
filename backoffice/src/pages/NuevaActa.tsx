import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { listSucursales } from "@/services/users";
import { createActa } from "@/services/actas";
import {
  findClienteByRut,
  listChecklistItems,
  listColores,
  listCombustibles,
  listComunas,
  listEquipoVentas,
  listEstadosChecklist,
  listTiposComision,
  listTiposVehiculo,
  listVehiculoMarcas,
  listVehiculoModelos,
  listVehiculoVersiones,
  lookupVehiculoByPpu,
} from "@/services/vehiculos";
import { useAuth } from "@/context/AuthContext";
import type { ActaCreateInput, ChecklistEntryInput } from "@/types";

type ChecklistState = Record<
  number,
  { presente: boolean; estado_checklist_id: number | ""; fecha_vencimiento: string; observacion: string }
>;

export default function NuevaActa() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const checklistQ = useQuery({ queryKey: ["checklist-items"], queryFn: listChecklistItems });
  const sucursalesQ = useQuery({ queryKey: ["sucursales"], queryFn: listSucursales });
  const marcasQ = useQuery({ queryKey: ["vehiculo-marcas"], queryFn: listVehiculoMarcas });
  const comunasQ = useQuery({ queryKey: ["comunas"], queryFn: listComunas });
  const tiposVehiculoQ = useQuery({ queryKey: ["tipos-vehiculo"], queryFn: listTiposVehiculo });
  const combustiblesQ = useQuery({ queryKey: ["combustibles"], queryFn: listCombustibles });
  const coloresQ = useQuery({ queryKey: ["colores"], queryFn: listColores });
  const estadosChecklistQ = useQuery({ queryKey: ["estados-checklist"], queryFn: listEstadosChecklist });
  const tiposComisionQ = useQuery({ queryKey: ["tipos-comision"], queryFn: listTiposComision });

  // La sucursal de recepción es la del usuario; solo se elige si no tiene una.
  const sucursalUsuario = user?.sucursal_id ?? null;

  const [cliente, setCliente] = useState({ rut: "", nombre: "", email: "", telefono: "", domicilio: "", comuna_id: "" as number | "" });
  const [veh, setVeh] = useState({
    ppu: "",
    marca_id: "" as number | "",
    modelo_id: "" as number | "",
    version_id: "" as number | "",
    anio: "", n_motor: "", n_chasis: "", km_ingreso: "",
    color_id: "" as number | "",
    tipo_vehiculo_id: "" as number | "",
    combustible_id: "" as number | "",
    sucursal_id: (sucursalUsuario ?? "") as number | "",
    derivar: false,
    sucursal_venta_id: "" as number | "",
    vendedor_id: "" as number | "",
  });
  const [orden, setOrden] = useState({ tipo_comision_id: "" as number | "", precio_venta_pactado: "", vigencia_dias: "30", exclusividad_abono: "40000" });
  const [observaciones, setObservaciones] = useState("");

  const comisionPreview = useMemo(() => {
    const tc = tiposComisionQ.data?.find((t) => t.id === orden.tipo_comision_id);
    const precio = Number(orden.precio_venta_pactado || 0);
    if (!tc || precio <= 0) return null;
    const comision = Math.max(Math.round(precio * tc.tasa), tc.minimo);
    return { comision, liquidacion: precio - comision };
  }, [tiposComisionQ.data, orden.tipo_comision_id, orden.precio_venta_pactado]);
  const [checklist, setChecklist] = useState<ChecklistState>({});
  const [error, setError] = useState<string | null>(null);
  const [rutHint, setRutHint] = useState<string | null>(null);
  const [ppuHint, setPpuHint] = useState<string | null>(null);
  const [ppuBloqueada, setPpuBloqueada] = useState(false);

  // Sucursal de origen efectiva (la del usuario, o la elegida si no tiene).
  const sucursalOrigen = sucursalUsuario ?? (veh.sucursal_id === "" ? null : Number(veh.sucursal_id));

  // Vendedores de la sucursal de venta (para nominar al derivar).
  const equipoVentaQ = useQuery({
    queryKey: ["equipo-ventas", veh.sucursal_venta_id],
    queryFn: () => listEquipoVentas(Number(veh.sucursal_venta_id)),
    enabled: veh.derivar && veh.sucursal_venta_id !== "",
  });

  const items = useMemo(
    () => (checklistQ.data ?? []).slice().sort((a, b) => a.orden - b.orden),
    [checklistQ.data],
  );

  const getRow = (id: number) =>
    checklist[id] ?? { presente: false, estado_checklist_id: "" as number | "", fecha_vencimiento: "", observacion: "" };
  const setRow = (id: number, patch: Partial<ChecklistState[number]>) =>
    setChecklist((c) => ({ ...c, [id]: { ...getRow(id), ...patch } }));

  const mut = useMutation({
    mutationFn: (input: ActaCreateInput) => createActa(input),
    onSuccess: () => navigate("/actas", { replace: true }),
    onError: (e: unknown) => setError(extractError(e)),
  });

  const findClienteMut = useMutation({ mutationFn: (rut: string) => findClienteByRut(rut) });
  const lookupVehiculoMut = useMutation({ mutationFn: (ppu: string) => lookupVehiculoByPpu(ppu) });

  const modelosQ = useQuery({
    queryKey: ["vehiculo-modelos", veh.marca_id],
    queryFn: () => listVehiculoModelos(Number(veh.marca_id)),
    enabled: veh.marca_id !== "",
  });
  const versionesQ = useQuery({
    queryKey: ["vehiculo-versiones", veh.modelo_id],
    queryFn: () => listVehiculoVersiones(Number(veh.modelo_id)),
    enabled: veh.modelo_id !== "",
  });

  // Autocompletar cliente por RUT mientras se escribe (con debounce).
  useEffect(() => {
    const rut = cliente.rut.trim();
    if (rut.length < 3) { setRutHint(null); return; }
    const h = window.setTimeout(async () => {
      try {
        const res = await findClienteMut.mutateAsync(rut);
        if (!res.found || !res.cliente) {
          setRutHint("Cliente nuevo: se creará al registrar el acta.");
          return;
        }
        const c = res.cliente;
        setCliente((prev) => ({
          ...prev,
          nombre: c.nombre ?? "", email: c.email ?? "", telefono: c.telefono ?? "",
          domicilio: c.domicilio ?? "", comuna_id: c.comuna_id ?? "",
        }));
        setRutHint("Cliente encontrado: datos cargados desde la base.");
      } catch {
        setRutHint(null);
      }
    }, 450);
    return () => window.clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cliente.rut]);

  // Autocompletar vehículo por PPU mientras se escribe (con debounce).
  useEffect(() => {
    const ppu = veh.ppu.trim().toUpperCase();
    setPpuBloqueada(false);
    if (ppu.length < 4) { setPpuHint(null); return; }
    const h = window.setTimeout(async () => {
      try {
        const res = await lookupVehiculoMut.mutateAsync(ppu);
        if (!res.found || !res.vehiculo) {
          setPpuHint("Patente nueva en este tenant. Completa los datos del vehículo.");
          return;
        }
        const v = res.vehiculo;
        // Precarga la ficha física conocida, incluyendo la cascada marca/modelo/versión.
        setVeh((prev) => ({
          ...prev,
          marca_id: v.marca_id, modelo_id: v.modelo_id, version_id: v.version_id,
          anio: String(v.anio), n_motor: v.n_motor ?? "", n_chasis: v.n_chasis ?? "",
          color_id: v.color_id ?? "",
        }));
        if (res.tiene_acta_activa) {
          setPpuBloqueada(true);
          setPpuHint(`Este auto (${v.marca} ${v.modelo}) ya tiene un acta VIGENTE. No puede recepcionarse hasta cerrarla.`);
        } else {
          setPpuHint(`Reingreso: ${v.marca} ${v.modelo} ya fue corretado antes (${res.total_actas} acta(s)). Datos precargados.`);
        }
      } catch {
        setPpuHint(null);
      }
    }, 450);
    return () => window.clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [veh.ppu]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (ppuBloqueada) { setError("Este vehículo ya tiene un acta vigente."); return; }
    if (sucursalOrigen === null) { setError("Selecciona la sucursal de recepción."); return; }
    if (veh.derivar && veh.sucursal_venta_id === "") { setError("Selecciona la sucursal a la que derivas la venta."); return; }
    if (veh.derivar && Number(veh.sucursal_venta_id) === sucursalOrigen) { setError("La sucursal de venta derivada debe ser distinta a la de recepción."); return; }
    if (veh.derivar && veh.vendedor_id === "") { setError("Indica el vendedor de la sucursal de venta."); return; }
    if (veh.version_id === "") { setError("Selecciona la versión del vehículo."); return; }
    if (orden.tipo_comision_id === "") { setError("Selecciona el tipo de comisión."); return; }

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
    mut.mutate({
      cliente: {
        rut: cliente.rut.trim(), nombre: cliente.nombre.trim(),
        email: cliente.email.trim() || null, telefono: cliente.telefono.trim() || null,
        domicilio: cliente.domicilio.trim() || null,
        comuna_id: cliente.comuna_id === "" ? null : Number(cliente.comuna_id),
      },
      ppu: veh.ppu.trim().toUpperCase(),
      version_id: Number(veh.version_id),
      anio: Number(veh.anio),
      n_motor: veh.n_motor.trim() || null,
      n_chasis: veh.n_chasis.trim() || null,
      color_id: veh.color_id === "" ? null : Number(veh.color_id),
      tipo_vehiculo_id: veh.tipo_vehiculo_id === "" ? null : Number(veh.tipo_vehiculo_id),
      combustible_id: veh.combustible_id === "" ? null : Number(veh.combustible_id),
      km_ingreso: Number(veh.km_ingreso || 0),
      // null -> el backend usa la sucursal del usuario autenticado.
      sucursal_id: sucursalUsuario === null ? Number(veh.sucursal_id) : null,
      sucursal_venta_id: veh.derivar ? Number(veh.sucursal_venta_id) : sucursalOrigen,
      vendedor_user_id: veh.derivar ? Number(veh.vendedor_id) : null,
      tipo_comision_id: Number(orden.tipo_comision_id),
      precio_venta_pactado: Number(orden.precio_venta_pactado || 0),
      vigencia_dias: Number(orden.vigencia_dias || 30),
      exclusividad_abono: Number(orden.exclusividad_abono || 0),
      observaciones: observaciones.trim() || null,
      checklist: checklistPayload,
    });
  }

  const nombreSucursalUsuario = sucursalesQ.data?.find((s) => s.id === sucursalUsuario)?.nombre;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold text-brand-ink">Nueva Acta de Recepción</h1>
      <p className="mb-6 text-sm text-brand-muted">
        El vehículo se registrará en estado <strong>RECEPCIONADO</strong> a tu nombre
        {nombreSucursalUsuario ? <> en <strong>{nombreSucursalUsuario}</strong></> : null}.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Section title="Antecedentes del Cliente">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="RUT" required value={cliente.rut} onChange={(v) => setCliente({ ...cliente, rut: v })} />
            <Input label="Nombre completo" required value={cliente.nombre} onChange={(v) => setCliente({ ...cliente, nombre: v })} />
            <Input label="Correo" type="email" value={cliente.email} onChange={(v) => setCliente({ ...cliente, email: v })} />
            <Input label="Teléfono" value={cliente.telefono} onChange={(v) => setCliente({ ...cliente, telefono: v })} />
            <Input label="Domicilio" value={cliente.domicilio} onChange={(v) => setCliente({ ...cliente, domicilio: v })} />
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Comuna</span>
              <select value={cliente.comuna_id} onChange={(e) => setCliente({ ...cliente, comuna_id: e.target.value === "" ? "" : Number(e.target.value) })} className={inputCls}>
                <option value="">Seleccionar</option>
                {comunasQ.data?.map((c) => (<option key={c.id} value={c.id}>{c.nombre}</option>))}
              </select>
            </label>
          </div>
          {rutHint && <p className="mt-2 text-sm text-brand-muted">{rutHint}</p>}
        </Section>

        <Section title="Antecedentes del Vehículo">
          <div className="grid gap-4 sm:grid-cols-3">
            <Input label="PPU (patente)" required value={veh.ppu} onChange={(v) => setVeh({ ...veh, ppu: v })} />
            <SelectField label="Marca" required value={veh.marca_id} onChange={(v) => setVeh({ ...veh, marca_id: v, modelo_id: "", version_id: "" })}
              options={(marcasQ.data ?? []).map((m) => ({ id: m.id, label: m.nombre }))} />
            <SelectField label="Modelo" required value={veh.modelo_id} disabled={veh.marca_id === ""} onChange={(v) => setVeh({ ...veh, modelo_id: v, version_id: "" })}
              options={(modelosQ.data ?? []).map((m) => ({ id: m.id, label: m.nombre }))} />
            <SelectField label="Versión" required value={veh.version_id} disabled={veh.modelo_id === ""} onChange={(v) => setVeh({ ...veh, version_id: v })}
              options={(versionesQ.data ?? []).map((v) => ({ id: v.id, label: v.nombre }))} />
            <Input label="Año" type="number" required value={veh.anio} onChange={(v) => setVeh({ ...veh, anio: v })} />
            <Input label="N° Motor" value={veh.n_motor} onChange={(v) => setVeh({ ...veh, n_motor: v })} />
            <Input label="N° Chasis" value={veh.n_chasis} onChange={(v) => setVeh({ ...veh, n_chasis: v })} />
            <Input label="Kilometraje de ingreso" type="number" value={veh.km_ingreso} onChange={(v) => setVeh({ ...veh, km_ingreso: v })} />
            <SelectField label="Tipo de vehículo" value={veh.tipo_vehiculo_id} onChange={(v) => setVeh({ ...veh, tipo_vehiculo_id: v })}
              options={(tiposVehiculoQ.data ?? []).map((t) => ({ id: t.id, label: t.nombre }))} />
            <SelectField label="Combustible" value={veh.combustible_id} onChange={(v) => setVeh({ ...veh, combustible_id: v })}
              options={(combustiblesQ.data ?? []).map((t) => ({ id: t.id, label: t.nombre }))} />
            <SelectField label="Color" value={veh.color_id} onChange={(v) => setVeh({ ...veh, color_id: v })}
              options={(coloresQ.data ?? []).map((c) => ({ id: c.id, label: c.nombre }))} />
            {sucursalUsuario === null && (
              <SelectField label="Sucursal de recepción" required value={veh.sucursal_id} onChange={(v) => setVeh({ ...veh, sucursal_id: v })}
                options={(sucursalesQ.data ?? []).map((s) => ({ id: s.id, label: s.nombre }))} />
            )}
          </div>
          {ppuHint && <p className={`mt-2 text-sm ${ppuBloqueada ? "text-red-600" : "text-brand-muted"}`}>{ppuHint}</p>}
        </Section>

        <Section title="Gestión de la Venta">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-brand-ink">
              <input type="radio" name="venta_modo" checked={!veh.derivar} onChange={() => setVeh({ ...veh, derivar: false, sucursal_venta_id: "", vendedor_id: "" })} />
              La venta la realizo yo (misma sucursal de recepción)
            </label>
            <label className="flex items-center gap-2 text-sm text-brand-ink">
              <input type="radio" name="venta_modo" checked={veh.derivar} onChange={() => setVeh({ ...veh, derivar: true })} />
              Derivar la venta a otra sucursal
            </label>
          </div>
          {veh.derivar && (
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <SelectField label="Sucursal de venta" required value={veh.sucursal_venta_id}
                onChange={(v) => setVeh({ ...veh, sucursal_venta_id: v, vendedor_id: "" })}
                options={(sucursalesQ.data ?? []).filter((s) => s.id !== sucursalOrigen).map((s) => ({ id: s.id, label: s.nombre }))} />
              <SelectField label="Vendedor que tomará la venta" required value={veh.vendedor_id} disabled={veh.sucursal_venta_id === ""}
                onChange={(v) => setVeh({ ...veh, vendedor_id: v })}
                options={(equipoVentaQ.data ?? []).map((u) => ({ id: u.id, label: u.nombre }))} />
              <p className="sm:col-span-2 text-xs text-brand-muted-2">
                El vendedor debe pertenecer a la sucursal de destino; él imprimirá el documento de firma al reunirse con el cliente.
              </p>
            </div>
          )}
        </Section>

        <Section title="Orden de Venta">
          <div className="grid gap-4 sm:grid-cols-3">
            <SelectField label="Tipo de comisión" required value={orden.tipo_comision_id} onChange={(v) => setOrden({ ...orden, tipo_comision_id: v })}
              options={(tiposComisionQ.data ?? []).map((t) => ({ id: t.id, label: `${t.nombre} (${(t.tasa * 100).toFixed(0)}%, mín $${t.minimo.toLocaleString("es-CL")})` }))} />
            <Input label="Precio de venta pactado (CLP)" type="number" required value={orden.precio_venta_pactado} onChange={(v) => setOrden({ ...orden, precio_venta_pactado: v })} />
            <Input label="Vigencia (días)" type="number" value={orden.vigencia_dias} onChange={(v) => setOrden({ ...orden, vigencia_dias: v })} />
            <Input label="Abono exclusividad (CLP)" type="number" value={orden.exclusividad_abono} onChange={(v) => setOrden({ ...orden, exclusividad_abono: v })} />
          </div>
          {comisionPreview && (
            <div className="mt-4 flex gap-6 rounded-lg bg-brand-surface p-3 text-sm">
              <span>Comisión: <strong className="text-brand-ink">${comisionPreview.comision.toLocaleString("es-CL")}</strong></span>
              <span>Liquidación de pago: <strong className="text-brand-ink">${comisionPreview.liquidacion.toLocaleString("es-CL")}</strong></span>
            </div>
          )}
        </Section>

        <Section title="Checklist de Documentos y Accesorios (12 puntos)">
          {checklistQ.isLoading && <p className="text-brand-muted">Cargando checklist…</p>}
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
                    {estadosChecklistQ.data?.map((es) => (<option key={es.id} value={es.id}>{es.nombre}</option>))}
                  </select>
                  {it.requiere_vencimiento ? (
                    <label className="sm:col-span-3 flex flex-col">
                      <span className="text-[10px] uppercase text-brand-muted-2">Vence</span>
                      <input type="date" value={r.fecha_vencimiento} onChange={(e) => setRow(it.id, { fecha_vencimiento: e.target.value })} className={inputCls} />
                    </label>
                  ) : (
                    <span className="sm:col-span-3" />
                  )}
                  <input placeholder="Observación" value={r.observacion} onChange={(e) => setRow(it.id, { observacion: e.target.value })} className={`${inputCls} sm:col-span-3`} />
                </div>
              );
            })}
          </div>
        </Section>

        <Section title="Observaciones">
          <textarea
            value={observaciones}
            onChange={(e) => setObservaciones(e.target.value)}
            rows={3}
            placeholder="Observaciones del acta (texto libre)…"
            className={inputCls}
          />
        </Section>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={() => navigate(-1)} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-white">Cancelar</button>
          <button type="submit" disabled={mut.isPending || ppuBloqueada} className="rounded-lg bg-brand-accent px-5 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
            {mut.isPending ? "Guardando…" : "Registrar recepción"}
          </button>
        </div>
      </form>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-brand-surface-2 bg-white p-5">
      <h2 className="mb-4 font-semibold text-brand-ink">{title}</h2>
      {children}
    </section>
  );
}

function Input({ label, value, onChange, type = "text", required = false }: {
  label: string; value: string; onChange: (v: string) => void; type?: string; required?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-brand-ink">{label}</span>
      <input type={type} required={required} value={value} onChange={(e) => onChange(e.target.value)} className={inputCls} />
    </label>
  );
}

function SelectField({ label, value, onChange, options, required = false, disabled = false }: {
  label: string; value: number | ""; onChange: (v: number | "") => void;
  options: { id: number; label: string }[]; required?: boolean; disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-brand-ink">{label}</span>
      <select value={value} required={required} disabled={disabled}
        onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls}>
        <option value="">{required ? "Seleccionar" : "Seleccionar"}</option>
        {options.map((o) => (<option key={o.id} value={o.id}>{o.label}</option>))}
      </select>
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo registrar la recepción. Revisa los datos.";
}

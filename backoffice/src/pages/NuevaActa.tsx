import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { listSucursales } from "@/services/users";
import {
  createActa,
  findClienteByRut,
  findVehiculoGlobalByPpu,
  listChecklistItems,
  listCombustibles,
  listComunas,
  listTiposComision,
  listTiposVehiculo,
  listVehiculoMarcas,
  listVehiculoModelos,
  listVehiculoVersiones,
} from "@/services/vehiculos";
import type { ActaCreateInput, ChecklistEntryInput } from "@/types";

type ChecklistState = Record<
  number,
  { presente: boolean; estado: string; fecha_vencimiento: string; observacion: string }
>;

export default function NuevaActa() {
  const navigate = useNavigate();
  const checklistQ = useQuery({ queryKey: ["checklist-items"], queryFn: listChecklistItems });
  const sucursalesQ = useQuery({ queryKey: ["sucursales"], queryFn: listSucursales });
  const marcasQ = useQuery({ queryKey: ["vehiculo-marcas"], queryFn: listVehiculoMarcas });
  const comunasQ = useQuery({ queryKey: ["comunas"], queryFn: listComunas });
  const tiposVehiculoQ = useQuery({ queryKey: ["tipos-vehiculo"], queryFn: listTiposVehiculo });
  const combustiblesQ = useQuery({ queryKey: ["combustibles"], queryFn: listCombustibles });
  const tiposComisionQ = useQuery({ queryKey: ["tipos-comision"], queryFn: listTiposComision });

  const [cliente, setCliente] = useState({ rut: "", nombre: "", email: "", telefono: "", domicilio: "", comuna_id: "" as number | "" });
  const [veh, setVeh] = useState({
    ppu: "",
    marca_id: "" as number | "",
    modelo_id: "" as number | "",
    version_id: "" as number | "",
    anio: "", n_motor: "", n_chasis: "", km_ingreso: "",
    color: "",
    tipo_vehiculo_id: "" as number | "",
    combustible_id: "" as number | "",
    sucursal_id: "" as number | "",
    derivar: false,
    sucursal_venta_id: "" as number | "",
  });
  const [orden, setOrden] = useState({ tipo_comision_id: "" as number | "", precio_venta_pactado: "", vigencia_dias: "30", exclusividad_abono: "40000" });

  // Vista previa de comisión y liquidación (mismo cálculo que el backend).
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

  const items = useMemo(
    () => (checklistQ.data ?? []).slice().sort((a, b) => a.orden - b.orden),
    [checklistQ.data],
  );

  const getRow = (id: number) =>
    checklist[id] ?? { presente: false, estado: "", fecha_vencimiento: "", observacion: "" };
  const setRow = (id: number, patch: Partial<ChecklistState[number]>) =>
    setChecklist((c) => ({ ...c, [id]: { ...getRow(id), ...patch } }));

  const mut = useMutation({
    mutationFn: (input: ActaCreateInput) => createActa(input),
    onSuccess: () => navigate("/captaciones", { replace: true }),
    onError: (e: unknown) => setError(extractError(e)),
  });

  const findClienteMut = useMutation({ mutationFn: (rut: string) => findClienteByRut(rut) });
  const findVehiculoMut = useMutation({ mutationFn: (ppu: string) => findVehiculoGlobalByPpu(ppu) });

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

  async function handleRutBlur() {
    const rut = cliente.rut.trim();
    if (rut.length < 3) {
      setRutHint(null);
      return;
    }
    try {
      const res = await findClienteMut.mutateAsync(rut);
      if (!res.found || !res.cliente) {
        setRutHint("Cliente no encontrado en este tenant. Se creará al registrar el acta.");
        return;
      }
      setCliente((prev) => ({
        ...prev,
        rut: res.cliente?.rut ?? prev.rut,
        nombre: res.cliente?.nombre ?? "",
        email: res.cliente?.email ?? "",
        telefono: res.cliente?.telefono ?? "",
        domicilio: res.cliente?.domicilio ?? "",
        comuna_id: res.cliente?.comuna_id ?? "",
      }));
      setRutHint("Cliente encontrado: datos cargados desde la base.");
    } catch {
      setRutHint("No se pudo buscar el cliente por RUT.");
    }
  }

  async function handlePpuBlur() {
    const ppu = veh.ppu.trim().toUpperCase();
    if (ppu.length < 4) {
      setPpuHint(null);
      return;
    }
    try {
      const res = await findVehiculoMut.mutateAsync(ppu);
      if (!res.found || !res.vehiculo) {
        setPpuHint("Patente no encontrada en la base global.");
        return;
      }
      setVeh((prev) => ({
        ...prev,
        ppu,
        marca_id: "",
        modelo_id: "",
        version_id: "",
        anio: String(res.vehiculo?.anio ?? ""),
        n_motor: res.vehiculo?.n_motor ?? "",
        n_chasis: res.vehiculo?.n_chasis ?? "",
      }));
      setPpuHint(`Patente encontrada en tenant ${res.vehiculo.tenant_nombre}. Datos del vehículo cargados.`);
    } catch {
      setPpuHint("No se pudo buscar la patente en la base global.");
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (veh.sucursal_id === "") {
      setError("Selecciona una sucursal.");
      return;
    }
    if (veh.derivar && veh.sucursal_venta_id === "") {
      setError("Selecciona la sucursal a la que derivas la venta.");
      return;
    }
    if (veh.derivar && veh.sucursal_venta_id === veh.sucursal_id) {
      setError("La sucursal de venta derivada debe ser distinta a la de recepción.");
      return;
    }
    if (veh.version_id === "") {
      setError("Selecciona la versión del vehículo.");
      return;
    }
    if (orden.tipo_comision_id === "") {
      setError("Selecciona el tipo de comisión.");
      return;
    }
    const checklistPayload: ChecklistEntryInput[] = items.map((it) => {
      const r = getRow(it.id);
      return {
        checklist_item_id: it.id,
        presente: r.presente,
        estado: r.estado || null,
        fecha_vencimiento: r.fecha_vencimiento || null,
        observacion: r.observacion || null,
      };
    });
    mut.mutate({
      cliente: {
        rut: cliente.rut.trim(),
        nombre: cliente.nombre.trim(),
        email: cliente.email.trim() || null,
        telefono: cliente.telefono.trim() || null,
        domicilio: cliente.domicilio.trim() || null,
        comuna_id: cliente.comuna_id === "" ? null : Number(cliente.comuna_id),
      },
      ppu: veh.ppu.trim().toUpperCase(),
      version_id: Number(veh.version_id),
      anio: Number(veh.anio),
      n_motor: veh.n_motor.trim() || null,
      n_chasis: veh.n_chasis.trim() || null,
      km_ingreso: Number(veh.km_ingreso || 0),
      color: veh.color.trim() || null,
      tipo_vehiculo_id: veh.tipo_vehiculo_id === "" ? null : Number(veh.tipo_vehiculo_id),
      combustible_id: veh.combustible_id === "" ? null : Number(veh.combustible_id),
      sucursal_id: Number(veh.sucursal_id),
      sucursal_venta_id: veh.derivar ? Number(veh.sucursal_venta_id) : Number(veh.sucursal_id),
      tipo_comision_id: Number(orden.tipo_comision_id),
      precio_venta_pactado: Number(orden.precio_venta_pactado || 0),
      vigencia_dias: Number(orden.vigencia_dias || 30),
      exclusividad_abono: Number(orden.exclusividad_abono || 0),
      checklist: checklistPayload,
    });
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold text-brand-ink">Nueva Acta de Recepción</h1>
      <p className="mb-6 text-sm text-brand-muted">
        El vehículo se registrará en estado <strong>RECEPCIONADO</strong> a tu nombre.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Section title="Antecedentes del Cliente">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="RUT"
              required
              value={cliente.rut}
              onChange={(v) => setCliente({ ...cliente, rut: v })}
              onBlur={handleRutBlur}
            />
            <Input label="Nombre completo" required value={cliente.nombre} onChange={(v) => setCliente({ ...cliente, nombre: v })} />
            <Input label="Correo" type="email" value={cliente.email} onChange={(v) => setCliente({ ...cliente, email: v })} />
            <Input label="Teléfono" value={cliente.telefono} onChange={(v) => setCliente({ ...cliente, telefono: v })} />
            <Input label="Domicilio" value={cliente.domicilio} onChange={(v) => setCliente({ ...cliente, domicilio: v })} />
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Comuna</span>
              <select
                value={cliente.comuna_id}
                onChange={(e) => setCliente({ ...cliente, comuna_id: e.target.value === "" ? "" : Number(e.target.value) })}
                className={inputCls}
              >
                <option value="">Seleccionar</option>
                {comunasQ.data?.map((c) => (<option key={c.id} value={c.id}>{c.nombre}</option>))}
              </select>
            </label>
          </div>
          {rutHint && <p className="mt-2 text-sm text-brand-muted">{rutHint}</p>}
        </Section>

        <Section title="Antecedentes del Vehículo">
          <div className="grid gap-4 sm:grid-cols-3">
            <Input
              label="PPU (patente)"
              required
              value={veh.ppu}
              onChange={(v) => setVeh({ ...veh, ppu: v })}
              onBlur={handlePpuBlur}
            />
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Marca</span>
              <select
                required
                value={veh.marca_id}
                onChange={(e) => setVeh({
                  ...veh,
                  marca_id: e.target.value === "" ? "" : Number(e.target.value),
                  modelo_id: "",
                  version_id: "",
                })}
                className={inputCls}
              >
                <option value="" disabled>Seleccionar</option>
                {marcasQ.data?.map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Modelo</span>
              <select
                required
                value={veh.modelo_id}
                onChange={(e) => setVeh({
                  ...veh,
                  modelo_id: e.target.value === "" ? "" : Number(e.target.value),
                  version_id: "",
                })}
                className={inputCls}
                disabled={veh.marca_id === ""}
              >
                <option value="" disabled>Seleccionar</option>
                {modelosQ.data?.map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Versión</span>
              <select
                required
                value={veh.version_id}
                onChange={(e) => setVeh({
                  ...veh,
                  version_id: e.target.value === "" ? "" : Number(e.target.value),
                })}
                className={inputCls}
                disabled={veh.modelo_id === ""}
              >
                <option value="" disabled>Seleccionar</option>
                {versionesQ.data?.map((v) => (
                  <option key={v.id} value={v.id}>{v.nombre}</option>
                ))}
              </select>
            </label>
            <Input label="Año" type="number" required value={veh.anio} onChange={(v) => setVeh({ ...veh, anio: v })} />
            <Input label="N° Motor" value={veh.n_motor} onChange={(v) => setVeh({ ...veh, n_motor: v })} />
            <Input label="N° Chasis" value={veh.n_chasis} onChange={(v) => setVeh({ ...veh, n_chasis: v })} />
            <Input label="Kilometraje de ingreso" type="number" value={veh.km_ingreso} onChange={(v) => setVeh({ ...veh, km_ingreso: v })} />
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Tipo de vehículo</span>
              <select
                value={veh.tipo_vehiculo_id}
                onChange={(e) => setVeh({ ...veh, tipo_vehiculo_id: e.target.value === "" ? "" : Number(e.target.value) })}
                className={inputCls}
              >
                <option value="">Seleccionar</option>
                {tiposVehiculoQ.data?.map((t) => (<option key={t.id} value={t.id}>{t.nombre}</option>))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Combustible</span>
              <select
                value={veh.combustible_id}
                onChange={(e) => setVeh({ ...veh, combustible_id: e.target.value === "" ? "" : Number(e.target.value) })}
                className={inputCls}
              >
                <option value="">Seleccionar</option>
                {combustiblesQ.data?.map((t) => (<option key={t.id} value={t.id}>{t.nombre}</option>))}
              </select>
            </label>
            <Input label="Color" value={veh.color} onChange={(v) => setVeh({ ...veh, color: v })} />
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Sucursal de recepción</span>
              <select
                required
                value={veh.sucursal_id}
                onChange={(e) => setVeh({ ...veh, sucursal_id: e.target.value === "" ? "" : Number(e.target.value) })}
                className={inputCls}
              >
                <option value="" disabled>Seleccionar</option>
                {sucursalesQ.data?.map((s) => (
                  <option key={s.id} value={s.id}>{s.nombre}</option>
                ))}
              </select>
            </label>
          </div>
          {ppuHint && <p className="mt-2 text-sm text-brand-muted">{ppuHint}</p>}
        </Section>

        <Section title="Gestión de la Venta">
          <p className="mb-3 text-sm text-brand-muted">
            Indica quién gestionará la venta de este vehículo.
          </p>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-brand-ink">
              <input
                type="radio"
                name="venta_modo"
                checked={!veh.derivar}
                onChange={() => setVeh({ ...veh, derivar: false, sucursal_venta_id: "" })}
              />
              La venta la realizo yo (misma sucursal de recepción)
            </label>
            <label className="flex items-center gap-2 text-sm text-brand-ink">
              <input
                type="radio"
                name="venta_modo"
                checked={veh.derivar}
                onChange={() => setVeh({ ...veh, derivar: true })}
              />
              Derivar la venta a otra sucursal
            </label>
          </div>
          {veh.derivar && (
            <label className="mt-3 block max-w-xs">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Sucursal de venta</span>
              <select
                value={veh.sucursal_venta_id}
                onChange={(e) => setVeh({ ...veh, sucursal_venta_id: e.target.value === "" ? "" : Number(e.target.value) })}
                className={inputCls}
              >
                <option value="" disabled>Seleccionar</option>
                {sucursalesQ.data
                  ?.filter((s) => s.id !== veh.sucursal_id)
                  .map((s) => (
                    <option key={s.id} value={s.id}>{s.nombre}</option>
                  ))}
              </select>
              <span className="mt-1 block text-xs text-brand-muted-2">
                Cualquier ejecutivo de esa sucursal podrá tomar y cerrar la venta.
              </span>
            </label>
          )}
        </Section>

        <Section title="Orden de Venta">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Tipo de comisión</span>
              <select
                required
                value={orden.tipo_comision_id}
                onChange={(e) => setOrden({ ...orden, tipo_comision_id: e.target.value === "" ? "" : Number(e.target.value) })}
                className={inputCls}
              >
                <option value="" disabled>Seleccionar</option>
                {tiposComisionQ.data?.map((t) => (
                  <option key={t.id} value={t.id}>{t.nombre} ({(t.tasa * 100).toFixed(0)}%, mín ${t.minimo.toLocaleString("es-CL")})</option>
                ))}
              </select>
            </label>
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
                    <span className="text-xs text-brand-muted-2">({it.tipo})</span>
                  </label>
                  <select value={r.estado} onChange={(e) => setRow(it.id, { estado: e.target.value })} className={`${inputCls} sm:col-span-2`}>
                    <option value="">Estado…</option>
                    <option value="OK">OK</option>
                    <option value="Observado">Observado</option>
                    <option value="Faltante">Faltante</option>
                  </select>
                  {it.requiere_vencimiento ? (
                    <input type="date" value={r.fecha_vencimiento} onChange={(e) => setRow(it.id, { fecha_vencimiento: e.target.value })} className={`${inputCls} sm:col-span-3`} />
                  ) : (
                    <span className="sm:col-span-3" />
                  )}
                  <input placeholder="Observación" value={r.observacion} onChange={(e) => setRow(it.id, { observacion: e.target.value })} className={`${inputCls} sm:col-span-3`} />
                </div>
              );
            })}
          </div>
        </Section>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={() => navigate(-1)} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-white">
            Cancelar
          </button>
          <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-5 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
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

function Input({
  label, value, onChange, type = "text", required = false, onBlur,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
  onBlur?: () => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-brand-ink">{label}</span>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        className={inputCls}
      />
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo registrar la recepción. Revisa los datos.";
}

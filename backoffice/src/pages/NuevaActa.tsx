import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { listSucursales } from "@/services/users";
import { createActa } from "@/services/actas";
import {
  findClienteByRut,
  listColores,
  listCombustibles,
  listComunas,
  listEquipoVentas,
  listTiposComision,
  listTiposVehiculo,
  listVehiculoMarcas,
  listVehiculoModelos,
  listVehiculoVersiones,
  lookupVehiculoByPpu,
} from "@/services/vehiculos";
import { useAuth } from "@/context/AuthContext";
import type { ActaCreateInput } from "@/types";

// Captación (online): se recogen datos del cliente y del vehículo. El checklist,
// N° motor/chasis, km y fotos se registran después, al recepcionar el auto.
export default function NuevaActa() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const sucursalesQ = useQuery({ queryKey: ["sucursales"], queryFn: listSucursales });
  const marcasQ = useQuery({ queryKey: ["vehiculo-marcas"], queryFn: listVehiculoMarcas });
  const comunasQ = useQuery({ queryKey: ["comunas"], queryFn: listComunas });
  const tiposVehiculoQ = useQuery({ queryKey: ["tipos-vehiculo"], queryFn: listTiposVehiculo });
  const combustiblesQ = useQuery({ queryKey: ["combustibles"], queryFn: listCombustibles });
  const coloresQ = useQuery({ queryKey: ["colores"], queryFn: listColores });
  const tiposComisionQ = useQuery({ queryKey: ["tipos-comision"], queryFn: listTiposComision });

  const sucursalUsuario = user?.sucursal_id ?? null;

  const [cliente, setCliente] = useState({ rut: "", nombre: "", email: "", telefono: "", domicilio: "", comuna_id: "" as number | "" });
  const [veh, setVeh] = useState({
    ppu: "",
    marca_id: "" as number | "",
    modelo_id: "" as number | "",
    version_id: "" as number | "",
    anio: "",
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
  const [error, setError] = useState<string | null>(null);
  const [rutHint, setRutHint] = useState<string | null>(null);
  const [ppuHint, setPpuHint] = useState<string | null>(null);
  const [ppuBloqueada, setPpuBloqueada] = useState(false);

  const sucursalOrigen = sucursalUsuario ?? (veh.sucursal_id === "" ? null : Number(veh.sucursal_id));

  const equipoVentaQ = useQuery({
    queryKey: ["equipo-ventas", veh.sucursal_venta_id],
    queryFn: () => listEquipoVentas(Number(veh.sucursal_venta_id)),
    enabled: veh.derivar && veh.sucursal_venta_id !== "",
  });

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

  // Autocompletar cliente por RUT mientras se escribe.
  useEffect(() => {
    const rut = cliente.rut.trim();
    if (rut.length < 3) { setRutHint(null); return; }
    const h = window.setTimeout(async () => {
      try {
        const res = await findClienteMut.mutateAsync(rut);
        if (!res.found || !res.cliente) { setRutHint("Cliente nuevo: se creará al captar."); return; }
        const c = res.cliente;
        setCliente((prev) => ({ ...prev, nombre: c.nombre ?? "", email: c.email ?? "", telefono: c.telefono ?? "", domicilio: c.domicilio ?? "", comuna_id: c.comuna_id ?? "" }));
        setRutHint("Cliente encontrado: datos cargados desde la base.");
      } catch { setRutHint(null); }
    }, 450);
    return () => window.clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cliente.rut]);

  // Autocompletar vehículo por PPU mientras se escribe.
  useEffect(() => {
    const ppu = veh.ppu.trim().toUpperCase();
    setPpuBloqueada(false);
    if (ppu.length < 4) { setPpuHint(null); return; }
    const h = window.setTimeout(async () => {
      try {
        const res = await lookupVehiculoMut.mutateAsync(ppu);
        if (!res.found || !res.vehiculo) { setPpuHint("Patente nueva en este tenant."); return; }
        const v = res.vehiculo;
        setVeh((prev) => ({ ...prev, marca_id: v.marca_id, modelo_id: v.modelo_id, version_id: v.version_id, anio: String(v.anio), color_id: v.color_id ?? "" }));
        if (res.tiene_acta_activa) {
          setPpuBloqueada(true);
          setPpuHint(`Este auto (${v.marca} ${v.modelo}) ya tiene un acta VIGENTE. No puede captarse hasta cerrarla.`);
        } else {
          setPpuHint(`Reingreso: ${v.marca} ${v.modelo} ya fue corretado antes (${res.total_actas} acta(s)).`);
        }
      } catch { setPpuHint(null); }
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
      // Datos físicos (motor/chasis/km) y checklist se completan al recepcionar.
      n_motor: null,
      n_chasis: null,
      color_id: veh.color_id === "" ? null : Number(veh.color_id),
      tipo_vehiculo_id: veh.tipo_vehiculo_id === "" ? null : Number(veh.tipo_vehiculo_id),
      combustible_id: veh.combustible_id === "" ? null : Number(veh.combustible_id),
      km_ingreso: 0,
      sucursal_id: sucursalUsuario === null ? Number(veh.sucursal_id) : null,
      sucursal_venta_id: veh.derivar ? Number(veh.sucursal_venta_id) : sucursalOrigen,
      vendedor_user_id: veh.derivar ? Number(veh.vendedor_id) : null,
      tipo_comision_id: Number(orden.tipo_comision_id),
      precio_venta_pactado: Number(orden.precio_venta_pactado || 0),
      vigencia_dias: Number(orden.vigencia_dias || 30),
      exclusividad_abono: Number(orden.exclusividad_abono || 0),
      observaciones: observaciones.trim() || null,
      checklist: [],
    });
  }

  const nombreSucursalUsuario = sucursalesQ.data?.find((s) => s.id === sucursalUsuario)?.nombre;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold text-brand-ink">Nueva Captación</h1>
      <p className="mb-6 text-sm text-brand-muted">
        Captación online del cliente y su vehículo. El auto quedará en estado <strong>CAPTADO</strong>
        {nombreSucursalUsuario ? <> en <strong>{nombreSucursalUsuario}</strong></> : null}. El checklist, N° motor/chasis, km y fotos se completan al <strong>recepcionar</strong> el auto en la sucursal.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Section title="Antecedentes del Cliente">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="RUT" required value={cliente.rut} onChange={(v) => setCliente({ ...cliente, rut: v })} />
            <Input label="Nombre completo" required value={cliente.nombre} onChange={(v) => setCliente({ ...cliente, nombre: v })} />
            <Input label="Correo" type="email" value={cliente.email} onChange={(v) => setCliente({ ...cliente, email: v })} />
            <Input label="Teléfono" value={cliente.telefono} onChange={(v) => setCliente({ ...cliente, telefono: v })} />
            <Input label="Domicilio" value={cliente.domicilio} onChange={(v) => setCliente({ ...cliente, domicilio: v })} />
            <SelectField label="Comuna" value={cliente.comuna_id} onChange={(v) => setCliente({ ...cliente, comuna_id: v })}
              options={(comunasQ.data ?? []).map((c) => ({ id: c.id, label: c.nombre }))} />
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
                El vendedor debe pertenecer a la sucursal de destino; él imprimirá el documento de firma al recepcionar el auto.
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

        <Section title="Observaciones">
          <textarea value={observaciones} onChange={(e) => setObservaciones(e.target.value)} rows={3} placeholder="Observaciones de la captación (texto libre)…" className={inputCls} />
        </Section>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={() => navigate(-1)} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-white">Cancelar</button>
          <button type="submit" disabled={mut.isPending || ppuBloqueada} className="rounded-lg bg-brand-accent px-5 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
            {mut.isPending ? "Guardando…" : "Registrar captación"}
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
        <option value="">Seleccionar</option>
        {options.map((o) => (<option key={o.id} value={o.id}>{o.label}</option>))}
      </select>
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo registrar la captación. Revisa los datos.";
}

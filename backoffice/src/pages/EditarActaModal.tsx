import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getActa, updateActa } from "@/services/actas";
import {
  listChecklistItems,
  listColores,
  listEquipoVentas,
  listEstadosChecklist,
  listTiposComision,
  listVehiculoMarcas,
  listVehiculoModelos,
  listVehiculoVersiones,
  updateVehiculo,
} from "@/services/vehiculos";
import { listSucursales } from "@/services/users";
import type { ChecklistEntryInput } from "@/types";

type ChecklistState = Record<
  number,
  { presente: boolean; estado_checklist_id: number | ""; fecha_vencimiento: string; observacion: string }
>;

/** Edición completa de un acta en RECEPCIONADO: cliente, ficha del auto,
 *  orden de venta, checklist, observaciones y vendedor nominado. */
export default function EditarActaModal({ actaId, onClose, onDone }: {
  actaId: number; onClose: () => void; onDone: () => void;
}) {
  const detalleQ = useQuery({ queryKey: ["acta", actaId], queryFn: () => getActa(actaId) });
  const sucursalesQ = useQuery({ queryKey: ["sucursales"], queryFn: listSucursales });
  const marcasQ = useQuery({ queryKey: ["vehiculo-marcas"], queryFn: listVehiculoMarcas });
  const coloresQ = useQuery({ queryKey: ["colores"], queryFn: listColores });
  const tiposComisionQ = useQuery({ queryKey: ["tipos-comision"], queryFn: listTiposComision });
  const checklistItemsQ = useQuery({ queryKey: ["checklist-items"], queryFn: listChecklistItems });
  const estadosChecklistQ = useQuery({ queryKey: ["estados-checklist"], queryFn: listEstadosChecklist });

  const [init, setInit] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Vehículo
  const [ppu, setPpu] = useState("");
  const [marcaId, setMarcaId] = useState<number | "">("");
  const [modeloId, setModeloId] = useState<number | "">("");
  const [versionId, setVersionId] = useState<number | "">("");
  const [anio, setAnio] = useState("");
  const [nMotor, setNMotor] = useState("");
  const [nChasis, setNChasis] = useState("");
  const [colorId, setColorId] = useState<number | "">("");
  // Acta
  const [sucursalVentaId, setSucursalVentaId] = useState<number | "">("");
  const [vendedorId, setVendedorId] = useState<number | "">("");
  const [km, setKm] = useState("");
  const [tipoComisionId, setTipoComisionId] = useState<number | "">("");
  const [precio, setPrecio] = useState("");
  const [vigencia, setVigencia] = useState("");
  const [abono, setAbono] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const [clienteNombre, setClienteNombre] = useState("");
  const [clienteEmail, setClienteEmail] = useState("");
  const [clienteTelefono, setClienteTelefono] = useState("");
  const [checklist, setChecklist] = useState<ChecklistState>({});
  // originales para detectar cambios de ficha
  const [orig, setOrig] = useState<{ ppu: string; version_id: number; anio: number; n_motor: string; n_chasis: string; color_id: number | "" } | null>(null);

  const modelosQ = useQuery({ queryKey: ["vehiculo-modelos", marcaId], queryFn: () => listVehiculoModelos(Number(marcaId)), enabled: marcaId !== "" });
  const versionesQ = useQuery({ queryKey: ["vehiculo-versiones", modeloId], queryFn: () => listVehiculoVersiones(Number(modeloId)), enabled: modeloId !== "" });

  const a = detalleQ.data;
  const sucursalOrigenId = a?.sucursal_id;
  const derivado = sucursalVentaId !== "" && Number(sucursalVentaId) !== sucursalOrigenId;
  const equipoQ = useQuery({
    queryKey: ["equipo-ventas", sucursalVentaId],
    queryFn: () => listEquipoVentas(Number(sucursalVentaId)),
    enabled: derivado,
  });

  useEffect(() => {
    if (!a || init) return;
    setPpu(a.vehiculo.ppu);
    setMarcaId(a.vehiculo.marca_id);
    setModeloId(a.vehiculo.modelo_id);
    setVersionId(a.vehiculo.version_id);
    setAnio(String(a.vehiculo.anio));
    setNMotor(a.vehiculo.n_motor ?? "");
    setNChasis(a.vehiculo.n_chasis ?? "");
    setColorId(a.vehiculo.color_id ?? "");
    setSucursalVentaId(a.sucursal_venta_id);
    setVendedorId(a.vendedor_user_id ?? "");
    setKm(String(a.km_ingreso));
    setTipoComisionId(a.tipo_comision ? tiposComisionQ.data?.find((t) => t.nombre === a.tipo_comision)?.id ?? "" : "");
    setPrecio(String(a.precio_venta_pactado));
    setVigencia(String(a.vigencia_dias));
    setAbono(String(a.exclusividad_abono));
    setObservaciones(a.observaciones ?? "");
    setClienteNombre(a.cliente_detalle.nombre);
    setClienteEmail(a.cliente_detalle.email ?? "");
    setClienteTelefono(a.cliente_detalle.telefono ?? "");
    const cl: ChecklistState = {};
    for (const c of a.checklist) {
      cl[c.checklist_item_id] = {
        presente: c.presente,
        estado_checklist_id: c.estado_checklist_id ?? "",
        fecha_vencimiento: c.fecha_vencimiento ?? "",
        observacion: c.observacion ?? "",
      };
    }
    setChecklist(cl);
    setOrig({ ppu: a.vehiculo.ppu, version_id: a.vehiculo.version_id, anio: a.vehiculo.anio, n_motor: a.vehiculo.n_motor ?? "", n_chasis: a.vehiculo.n_chasis ?? "", color_id: a.vehiculo.color_id ?? "" });
    setInit(true);
  }, [a, init, tiposComisionQ.data]);

  // Al recuperar tipos de comisión después del init, fijar el id si faltaba.
  useEffect(() => {
    if (a && tipoComisionId === "" && tiposComisionQ.data && a.tipo_comision) {
      const t = tiposComisionQ.data.find((x) => x.nombre === a.tipo_comision);
      if (t) setTipoComisionId(t.id);
    }
  }, [a, tipoComisionId, tiposComisionQ.data]);

  const items = useMemo(() => (checklistItemsQ.data ?? []).slice().sort((x, y) => x.orden - y.orden), [checklistItemsQ.data]);
  const getRow = (id: number) => checklist[id] ?? { presente: false, estado_checklist_id: "" as number | "", fecha_vencimiento: "", observacion: "" };
  const setRow = (id: number, patch: Partial<ChecklistState[number]>) => setChecklist((c) => ({ ...c, [id]: { ...getRow(id), ...patch } }));

  const mut = useMutation({
    mutationFn: async () => {
      // 1) Ficha del auto: solo si cambió algo (evita 403 innecesario por historial).
      const fichaCambio = orig && (
        ppu.trim().toUpperCase() !== orig.ppu || Number(versionId) !== orig.version_id ||
        Number(anio) !== orig.anio || nMotor.trim() !== orig.n_motor ||
        nChasis.trim() !== orig.n_chasis || (colorId === "" ? null : Number(colorId)) !== (orig.color_id === "" ? null : orig.color_id)
      );
      if (fichaCambio && a) {
        await updateVehiculo(a.vehiculo_id, {
          ppu: ppu.trim().toUpperCase(),
          version_id: versionId === "" ? undefined : Number(versionId),
          anio: Number(anio),
          n_motor: nMotor.trim() || null,
          n_chasis: nChasis.trim() || null,
          color_id: colorId === "" ? null : Number(colorId),
        });
      }
      // 2) Datos del acta + checklist.
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
      await updateActa(actaId, {
        sucursal_venta_id: sucursalVentaId === "" ? undefined : Number(sucursalVentaId),
        vendedor_user_id: derivado ? (vendedorId === "" ? null : Number(vendedorId)) : null,
        km_ingreso: Number(km || 0),
        tipo_comision_id: tipoComisionId === "" ? undefined : Number(tipoComisionId),
        precio_venta_pactado: Number(precio || 0),
        vigencia_dias: Number(vigencia || 30),
        exclusividad_abono: Number(abono || 0),
        observaciones: observaciones.trim() || null,
        cliente_nombre: clienteNombre.trim(),
        cliente_email: clienteEmail.trim() || null,
        cliente_telefono: clienteTelefono.trim() || null,
        checklist: checklistPayload,
      });
    },
    onSuccess: onDone,
    onError: (e: unknown) => setError(extractError(e)),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4" onClick={onClose}>
      <div className="my-6 w-full max-w-3xl rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-brand-ink">Editar acta (RECEPCIONADO)</h2>
        {detalleQ.isLoading && <p className="mt-3 text-sm text-brand-muted">Cargando…</p>}
        {a && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setError(null);
              if (!clienteNombre.trim()) { setError("Nombre de cliente requerido."); return; }
              if (versionId === "") { setError("Selecciona marca/modelo/versión."); return; }
              if (derivado && vendedorId === "") { setError("Indica el vendedor de la sucursal de venta."); return; }
              mut.mutate();
            }}
            className="mt-4 space-y-5"
          >
            <fieldset className="grid gap-3 sm:grid-cols-3">
              <legend className="mb-1 text-sm font-semibold text-brand-ink">Vehículo</legend>
              <Text label="PPU" value={ppu} onChange={setPpu} />
              <Sel label="Marca" value={marcaId} onChange={(v) => { setMarcaId(v); setModeloId(""); setVersionId(""); }} opts={(marcasQ.data ?? []).map((m) => ({ id: m.id, label: m.nombre }))} />
              <Sel label="Modelo" value={modeloId} disabled={marcaId === ""} onChange={(v) => { setModeloId(v); setVersionId(""); }} opts={(modelosQ.data ?? []).map((m) => ({ id: m.id, label: m.nombre }))} />
              <Sel label="Versión" value={versionId} disabled={modeloId === ""} onChange={setVersionId} opts={(versionesQ.data ?? []).map((v) => ({ id: v.id, label: v.nombre }))} />
              <Text label="Año" type="number" value={anio} onChange={setAnio} />
              <Text label="N° Motor" value={nMotor} onChange={setNMotor} />
              <Text label="N° Chasis" value={nChasis} onChange={setNChasis} />
              <Sel label="Color" value={colorId} onChange={setColorId} opts={(coloresQ.data ?? []).map((c) => ({ id: c.id, label: c.nombre }))} />
            </fieldset>

            <fieldset className="grid gap-3 sm:grid-cols-3">
              <legend className="mb-1 text-sm font-semibold text-brand-ink">Orden de venta</legend>
              <Sel label="Tipo de comisión" value={tipoComisionId} onChange={setTipoComisionId} opts={(tiposComisionQ.data ?? []).map((t) => ({ id: t.id, label: t.nombre }))} />
              <Text label="Precio pactado" type="number" value={precio} onChange={setPrecio} />
              <Text label="Vigencia días" type="number" value={vigencia} onChange={setVigencia} />
              <Text label="Abono exclusividad" type="number" value={abono} onChange={setAbono} />
              <Text label="KM ingreso" type="number" value={km} onChange={setKm} />
              <Sel label="Sucursal de venta" value={sucursalVentaId} onChange={(v) => { setSucursalVentaId(v); setVendedorId(""); }} opts={(sucursalesQ.data ?? []).map((s) => ({ id: s.id, label: s.nombre }))} />
              {derivado && (
                <Sel label="Vendedor (sucursal de venta)" value={vendedorId} onChange={setVendedorId} opts={(equipoQ.data ?? []).map((u) => ({ id: u.id, label: u.nombre }))} />
              )}
            </fieldset>

            <fieldset className="grid gap-3 sm:grid-cols-3">
              <legend className="mb-1 text-sm font-semibold text-brand-ink">Cliente</legend>
              <Text label="Nombre" value={clienteNombre} onChange={setClienteNombre} />
              <Text label="Email" type="email" value={clienteEmail} onChange={setClienteEmail} />
              <Text label="Teléfono" value={clienteTelefono} onChange={setClienteTelefono} />
            </fieldset>

            <div>
              <p className="mb-2 text-sm font-semibold text-brand-ink">Checklist</p>
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
                        <input type="date" value={r.fecha_vencimiento} onChange={(e) => setRow(it.id, { fecha_vencimiento: e.target.value })} className={`${inputCls} sm:col-span-3`} />
                      ) : (<span className="sm:col-span-3" />)}
                      <input placeholder="Observación" value={r.observacion} onChange={(e) => setRow(it.id, { observacion: e.target.value })} className={`${inputCls} sm:col-span-3`} />
                    </div>
                  );
                })}
              </div>
            </div>

            <label className="block">
              <span className="mb-1 block text-sm font-semibold text-brand-ink">Observaciones</span>
              <textarea value={observaciones} onChange={(e) => setObservaciones(e.target.value)} rows={2} className={inputCls} />
            </label>

            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">Cancelar</button>
              <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
                {mut.isPending ? "Guardando…" : "Guardar cambios"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function Text({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-brand-muted">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className={inputCls} />
    </label>
  );
}

function Sel({ label, value, onChange, opts, disabled = false }: {
  label: string; value: number | ""; onChange: (v: number | "") => void; opts: { id: number; label: string }[]; disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-brand-muted">{label}</span>
      <select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))} className={inputCls}>
        <option value="">Seleccionar</option>
        {opts.map((o) => (<option key={o.id} value={o.id}>{o.label}</option>))}
      </select>
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo guardar el acta.";
}

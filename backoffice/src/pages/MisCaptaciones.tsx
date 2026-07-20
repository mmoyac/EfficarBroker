import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  aceptarTerminos,
  deleteVehiculo,
  downloadDocumentoFirma,
  getVehiculo,
  listEquipoVentas,
  listVehiculoMarcas,
  listVehiculoModelos,
  listVehiculoVersiones,
  listVehiculos,
  registrarVenta,
  updateVehiculo,
} from "@/services/vehiculos";
import { listSucursales } from "@/services/users";
import type { Vehiculo } from "@/types";

const ESTADO_STYLES: Record<string, string> = {
  RECEPCIONADO: "bg-blue-100 text-blue-700",
  CONTRATO_ACEPTADO: "bg-amber-100 text-amber-700",
  PUBLICADO: "bg-green-100 text-green-700",
  VENDIDO: "bg-purple-100 text-purple-700",
  PROSPECTO: "bg-gray-100 text-gray-600",
};

const VENDIBLE = new Set(["CONTRATO_ACEPTADO", "PUBLICADO"]);
const DOC_FIRMA = new Set(["CONTRATO_ACEPTADO", "PUBLICADO", "VENDIDO"]);

export default function MisCaptaciones() {
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["vehiculos", "mine"],
    queryFn: () => listVehiculos(true),
  });

  const [ventaFor, setVentaFor] = useState<Vehiculo | null>(null);
  const [editFor, setEditFor] = useState<Vehiculo | null>(null);

  const aceptarMut = useMutation({
    mutationFn: (v: Vehiculo) => aceptarTerminos(v.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vehiculos"] }),
    onError: (e: unknown) => alert(extractError(e)),
  });

  const eliminarMut = useMutation({
    mutationFn: (v: Vehiculo) => deleteVehiculo(v.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vehiculos"] }),
    onError: (e: unknown) => alert(extractError(e)),
  });

  const documentoMut = useMutation({
    mutationFn: async (v: Vehiculo) => {
      const blob = await downloadDocumentoFirma(v.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
    },
    onError: (e: unknown) => alert(extractError(e)),
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">Mis Captaciones</h1>
          <p className="text-sm text-brand-muted">Vehículos que has recepcionado</p>
        </div>
        <Link
          to="/actas/nueva"
          className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600"
        >
          + Nueva Acta de Recepción
        </Link>
      </div>

      {isLoading && <p className="text-brand-muted">Cargando…</p>}
      {isError && <p className="text-red-600">No se pudieron cargar tus captaciones.</p>}

      {data && data.length === 0 && (
        <div className="rounded-xl border border-dashed border-brand-surface-2 bg-white p-10 text-center">
          <p className="text-brand-muted">Aún no tienes vehículos recepcionados.</p>
          <Link to="/actas/nueva" className="mt-2 inline-block font-medium text-brand-accent-600 hover:underline">
            Levanta tu primera acta →
          </Link>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-brand-surface-2 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-4 py-3 font-medium">PPU</th>
                <th className="px-4 py-3 font-medium">Vehículo</th>
                <th className="px-4 py-3 font-medium">Cliente</th>
                <th className="px-4 py-3 font-medium">Captador</th>
                <th className="px-4 py-3 font-medium">Vendedor</th>
                <th className="px-4 py-3 font-medium">Precio</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.map((v) => (
                <tr key={v.id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-4 py-3 font-mono font-medium text-brand-ink">{v.ppu}</td>
                  <td className="px-4 py-3">
                    {v.marca} {v.modelo} <span className="text-brand-muted">{v.anio}</span>
                    {v.derivado && (
                      <span className="ml-2 rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700">
                        Derivado → {v.sucursal_venta}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-brand-muted">{v.cliente}</td>
                  <td className="px-4 py-3">{v.captador}</td>
                  <td className="px-4 py-3">{v.vendedor ?? <span className="text-brand-muted-2">—</span>}</td>
                  <td className="px-4 py-3">
                    ${(v.precio_venta_final ?? v.precio_venta_pactado).toLocaleString("es-CL")}
                    {v.precio_venta_final != null && (
                      <span className="ml-1 text-xs text-brand-muted-2">(final)</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_STYLES[v.estado_code] ?? "bg-gray-100 text-gray-600"}`}>
                      {v.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2 text-xs">
                      {v.estado_code === "RECEPCIONADO" && (
                        <>
                          <button
                            onClick={() => setEditFor(v)}
                            disabled={aceptarMut.isPending || eliminarMut.isPending}
                            className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => aceptarMut.mutate(v)}
                            disabled={aceptarMut.isPending || eliminarMut.isPending}
                            className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                          >
                            Aceptar términos
                          </button>
                          <button
                            onClick={() => {
                              if (window.confirm(`¿Eliminar captación ${v.ppu}? Esta acción no se puede deshacer.`)) {
                                eliminarMut.mutate(v);
                              }
                            }}
                            disabled={aceptarMut.isPending || eliminarMut.isPending}
                            className="rounded border border-red-200 px-2 py-1 text-red-700 hover:bg-red-50 disabled:opacity-60"
                          >
                            Eliminar
                          </button>
                        </>
                      )}
                      {VENDIBLE.has(v.estado_code) && (
                        <button
                          onClick={() => setVentaFor(v)}
                          className="rounded bg-brand-accent px-2 py-1 font-medium text-black hover:bg-brand-accent-600"
                        >
                          Registrar venta
                        </button>
                      )}
                      {DOC_FIRMA.has(v.estado_code) && (
                        <button
                          onClick={() => documentoMut.mutate(v)}
                          disabled={documentoMut.isPending}
                          className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface disabled:opacity-60"
                        >
                          PDF firma
                        </button>
                      )}
                      {![("RECEPCIONADO"), ...VENDIBLE, ...DOC_FIRMA].includes(v.estado_code) && (
                        <span className="text-brand-muted-2">—</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {ventaFor && (
        <RegistrarVentaModal vehiculo={ventaFor} onClose={() => setVentaFor(null)} onDone={() => {
          setVentaFor(null);
          qc.invalidateQueries({ queryKey: ["vehiculos"] });
        }} />
      )}

      {editFor && (
        <EditarCaptacionModal
          vehiculoId={editFor.id}
          onClose={() => setEditFor(null)}
          onDone={() => {
            setEditFor(null);
            qc.invalidateQueries({ queryKey: ["vehiculos"] });
          }}
        />
      )}
    </div>
  );
}

function EditarCaptacionModal({
  vehiculoId, onClose, onDone,
}: {
  vehiculoId: number; onClose: () => void; onDone: () => void;
}) {
  const detalleQ = useQuery({ queryKey: ["vehiculo", vehiculoId], queryFn: () => getVehiculo(vehiculoId) });

  const [ppu, setPpu] = useState("");
  const [marcaId, setMarcaId] = useState<number | "">("");
  const [modeloId, setModeloId] = useState<number | "">("");
  const [versionId, setVersionId] = useState<number | "">("");
  const [sucursalId, setSucursalId] = useState<number | "">("");
  const [sucursalVentaId, setSucursalVentaId] = useState<number | "">("");
  const [anio, setAnio] = useState("");
  const [km, setKm] = useState("");
  const [nMotor, setNMotor] = useState("");
  const [nChasis, setNChasis] = useState("");
  const [precio, setPrecio] = useState("");
  const [vigencia, setVigencia] = useState("");
  const [abono, setAbono] = useState("");
  const [clienteNombre, setClienteNombre] = useState("");
  const [clienteEmail, setClienteEmail] = useState("");
  const [clienteTelefono, setClienteTelefono] = useState("");
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const marcasQ = useQuery({ queryKey: ["vehiculo-marcas"], queryFn: listVehiculoMarcas });
  const sucursalesQ = useQuery({ queryKey: ["sucursales"], queryFn: listSucursales });
  const modelosQ = useQuery({
    queryKey: ["vehiculo-modelos", marcaId],
    queryFn: () => listVehiculoModelos(Number(marcaId)),
    enabled: marcaId !== "",
  });
  const versionesQ = useQuery({
    queryKey: ["vehiculo-versiones", modeloId],
    queryFn: () => listVehiculoVersiones(Number(modeloId)),
    enabled: modeloId !== "",
  });

  useEffect(() => {
    if (!detalleQ.data || initialized) return;
    setPpu(detalleQ.data.ppu);
    setVersionId(detalleQ.data.version_id ?? "");
    setSucursalId(detalleQ.data.sucursal_id);
    setSucursalVentaId(detalleQ.data.sucursal_venta_id);
    setAnio(String(detalleQ.data.anio));
    setKm(String(detalleQ.data.km_ingreso));
    setNMotor(detalleQ.data.n_motor ?? "");
    setNChasis(detalleQ.data.n_chasis ?? "");
    setPrecio(String(detalleQ.data.precio_venta_pactado));
    setVigencia(String(detalleQ.data.vigencia_dias));
    setAbono(String(detalleQ.data.exclusividad_abono));
    setClienteNombre(detalleQ.data.cliente_detalle.nombre);
    setClienteEmail(detalleQ.data.cliente_detalle.email ?? "");
    setClienteTelefono(detalleQ.data.cliente_detalle.telefono ?? "");
    setInitialized(true);
  }, [detalleQ.data, initialized]);

  useEffect(() => {
    if (!detalleQ.data || !marcasQ.data || marcaId !== "") return;
    const found = marcasQ.data.find((m) => m.nombre.toLowerCase() === detalleQ.data.marca.toLowerCase());
    if (found) setMarcaId(found.id);
  }, [detalleQ.data, marcasQ.data, marcaId]);

  useEffect(() => {
    if (!detalleQ.data || !modelosQ.data || modeloId !== "") return;
    const found = modelosQ.data.find((m) => m.nombre.toLowerCase() === detalleQ.data.modelo.toLowerCase());
    if (found) setModeloId(found.id);
  }, [detalleQ.data, modelosQ.data, modeloId]);

  useEffect(() => {
    if (!detalleQ.data || !versionesQ.data) return;
    if (detalleQ.data.version_id != null) {
      const byId = versionesQ.data.find((v) => v.id === detalleQ.data.version_id);
      if (byId) {
        setVersionId(byId.id);
        return;
      }
    }
    if (versionId === "") {
      const byName = versionesQ.data.find((v) => (detalleQ.data.version ?? "").toLowerCase() === v.nombre.toLowerCase());
      if (byName) setVersionId(byName.id);
    }
  }, [detalleQ.data, versionesQ.data, versionId]);

  const mut = useMutation({
    mutationFn: () => updateVehiculo(vehiculoId, {
      ppu: ppu.trim().toUpperCase(),
      anio: Number(anio),
      km_ingreso: Number(km || 0),
      n_motor: nMotor.trim() || null,
      n_chasis: nChasis.trim() || null,
      version_id: versionId === "" ? undefined : Number(versionId),
      sucursal_id: sucursalId === "" ? undefined : Number(sucursalId),
      sucursal_venta_id: sucursalVentaId === "" ? undefined : Number(sucursalVentaId),
      precio_venta_pactado: Number(precio || 0),
      vigencia_dias: Number(vigencia || 30),
      exclusividad_abono: Number(abono || 0),
      cliente_nombre: clienteNombre.trim(),
      cliente_email: clienteEmail.trim() || null,
      cliente_telefono: clienteTelefono.trim() || null,
    }),
    onSuccess: onDone,
    onError: (e: unknown) => setError(extractError(e)),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-brand-ink">Editar captación (RECEPCIONADO)</h2>
        {detalleQ.isLoading && <p className="mt-3 text-sm text-brand-muted">Cargando datos...</p>}
        {detalleQ.isError && <p className="mt-3 text-sm text-red-600">No se pudo cargar el detalle.</p>}
        {detalleQ.data && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setError(null);
              if (ppu.trim().length < 4) {
                setError("PPU inválida.");
                return;
              }
              if (!clienteNombre.trim()) {
                setError("Nombre de cliente requerido.");
                return;
              }
              if (versionId === "") {
                setError("Selecciona marca/modelo/versión.");
                return;
              }
              if (sucursalId === "") {
                setError("Selecciona una sucursal.");
                return;
              }
              mut.mutate();
            }}
            className="mt-4 grid gap-3 sm:grid-cols-2"
          >
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">PPU</span><input value={ppu} onChange={(e) => setPpu(e.target.value)} className={inputCls} required /></label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Marca</span>
              <select
                value={marcaId}
                onChange={(e) => {
                  setMarcaId(e.target.value === "" ? "" : Number(e.target.value));
                  setModeloId("");
                  setVersionId("");
                }}
                className={inputCls}
                required
              >
                <option value="" disabled>Seleccionar</option>
                {marcasQ.data?.map((m) => (<option key={m.id} value={m.id}>{m.nombre}</option>))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Modelo</span>
              <select
                value={modeloId}
                onChange={(e) => {
                  setModeloId(e.target.value === "" ? "" : Number(e.target.value));
                  setVersionId("");
                }}
                className={inputCls}
                disabled={marcaId === ""}
                required
              >
                <option value="" disabled>Seleccionar</option>
                {modelosQ.data?.map((m) => (<option key={m.id} value={m.id}>{m.nombre}</option>))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Versión</span>
              <select
                value={versionId}
                onChange={(e) => setVersionId(e.target.value === "" ? "" : Number(e.target.value))}
                className={inputCls}
                disabled={modeloId === ""}
                required
              >
                <option value="" disabled>Seleccionar</option>
                {versionesQ.data?.map((v) => (<option key={v.id} value={v.id}>{v.nombre}</option>))}
              </select>
            </label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Año</span><input type="number" value={anio} onChange={(e) => setAnio(e.target.value)} className={inputCls} required /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">KM ingreso</span><input type="number" value={km} onChange={(e) => setKm(e.target.value)} className={inputCls} required /></label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Sucursal de recepción</span>
              <select
                value={sucursalId}
                onChange={(e) => setSucursalId(e.target.value === "" ? "" : Number(e.target.value))}
                className={inputCls}
                required
              >
                <option value="" disabled>Seleccionar</option>
                {sucursalesQ.data?.map((s) => (<option key={s.id} value={s.id}>{s.nombre}</option>))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-brand-ink">Sucursal de venta</span>
              <select
                value={sucursalVentaId}
                onChange={(e) => setSucursalVentaId(e.target.value === "" ? "" : Number(e.target.value))}
                className={inputCls}
                required
              >
                <option value="" disabled>Seleccionar</option>
                {sucursalesQ.data?.map((s) => (<option key={s.id} value={s.id}>{s.nombre}</option>))}
              </select>
            </label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Precio pactado</span><input type="number" value={precio} onChange={(e) => setPrecio(e.target.value)} className={inputCls} required /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Vigencia días</span><input type="number" value={vigencia} onChange={(e) => setVigencia(e.target.value)} className={inputCls} required /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Abono exclusividad</span><input type="number" value={abono} onChange={(e) => setAbono(e.target.value)} className={inputCls} required /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">N° Motor</span><input value={nMotor} onChange={(e) => setNMotor(e.target.value)} className={inputCls} /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">N° Chasis</span><input value={nChasis} onChange={(e) => setNChasis(e.target.value)} className={inputCls} /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Cliente</span><input value={clienteNombre} onChange={(e) => setClienteNombre(e.target.value)} className={inputCls} required /></label>
            <label className="block"><span className="mb-1 block text-sm font-medium text-brand-ink">Email cliente</span><input type="email" value={clienteEmail} onChange={(e) => setClienteEmail(e.target.value)} className={inputCls} /></label>
            <label className="block sm:col-span-2"><span className="mb-1 block text-sm font-medium text-brand-ink">Teléfono cliente</span><input value={clienteTelefono} onChange={(e) => setClienteTelefono(e.target.value)} className={inputCls} /></label>

            {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}

            <div className="sm:col-span-2 mt-2 flex justify-end gap-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">
                Cancelar
              </button>
              <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
                {mut.isPending ? "Guardando..." : "Guardar cambios"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function RegistrarVentaModal({
  vehiculo, onClose, onDone,
}: {
  vehiculo: Vehiculo; onClose: () => void; onDone: () => void;
}) {
  const equipoQ = useQuery({ queryKey: ["equipo-ventas"], queryFn: listEquipoVentas });
  const [vendedorId, setVendedorId] = useState<number | "">("");
  const [precio, setPrecio] = useState(String(vehiculo.precio_venta_pactado));
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: () => registrarVenta(vehiculo.id, Number(vendedorId), Number(precio || 0)),
    onSuccess: onDone,
    onError: (e: unknown) => setError(extractError(e)),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-brand-ink">Registrar venta</h2>
        <p className="mb-4 text-sm text-brand-muted">
          {vehiculo.ppu} · {vehiculo.marca} {vehiculo.modelo} · captado por {vehiculo.captador}
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            if (vendedorId === "") {
              setError("Selecciona al vendedor.");
              return;
            }
            mut.mutate();
          }}
          className="space-y-3"
        >
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Vendedor (cierra la venta)</span>
            <select
              value={vendedorId}
              onChange={(e) => setVendedorId(e.target.value === "" ? "" : Number(e.target.value))}
              className={inputCls}
              required
            >
              <option value="" disabled>Seleccionar ejecutivo</option>
              {equipoQ.data?.map((u) => (
                <option key={u.id} value={u.id}>{u.nombre}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-brand-ink">Precio de venta final (CLP)</span>
            <input
              type="number"
              value={precio}
              onChange={(e) => setPrecio(e.target.value)}
              className={inputCls}
              required
            />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="mt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface">
              Cancelar
            </button>
            <button type="submit" disabled={mut.isPending} className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60">
              {mut.isPending ? "Registrando…" : "Confirmar venta"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "No se pudo completar la acción.";
}

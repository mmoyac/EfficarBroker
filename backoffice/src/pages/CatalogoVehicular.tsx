import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import { listVehiculoMarcas, listVehiculoModelos, listVehiculoVersiones } from "@/services/vehiculos";
import {
  createVehiculoMarca,
  createVehiculoModelo,
  createVehiculoVersion,
  deleteVehiculoMarca,
  deleteVehiculoModelo,
  deleteVehiculoVersion,
  updateVehiculoMarca,
  updateVehiculoModelo,
  updateVehiculoVersion,
} from "@/services/catalogoVehicular";

export default function CatalogoVehicular() {
  const { isSuperAdmin } = useAuth();
  const qc = useQueryClient();
  const [marcaId, setMarcaId] = useState<number | "">("");
  const [modeloId, setModeloId] = useState<number | "">("");

  const marcasQ = useQuery({ queryKey: ["vehiculo-marcas"], queryFn: listVehiculoMarcas });
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

  const selectedMarca = useMemo(
    () => marcasQ.data?.find((m) => m.id === marcaId) ?? null,
    [marcasQ.data, marcaId],
  );
  const selectedModelo = useMemo(
    () => modelosQ.data?.find((m) => m.id === modeloId) ?? null,
    [modelosQ.data, modeloId],
  );

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["vehiculo-marcas"] });
    qc.invalidateQueries({ queryKey: ["vehiculo-modelos"] });
    qc.invalidateQueries({ queryKey: ["vehiculo-versiones"] });
  };

  const createMarcaMut = useMutation({
    mutationFn: (nombre: string) => createVehiculoMarca(nombre),
    onSuccess: invalidate,
  });
  const createModeloMut = useMutation({
    mutationFn: ({ mid, nombre }: { mid: number; nombre: string }) => createVehiculoModelo(mid, nombre),
    onSuccess: invalidate,
  });
  const createVersionMut = useMutation({
    mutationFn: ({ mid, nombre }: { mid: number; nombre: string }) => createVehiculoVersion(mid, nombre),
    onSuccess: invalidate,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-ink">Catálogo Vehicular</h1>
        <p className="text-sm text-brand-muted">Administra marcas, modelos y versiones globales de la plataforma.</p>
        {!isSuperAdmin && (
          <p className="mt-1 text-xs text-brand-muted">Modo lectura: solo SuperAdmin puede crear, editar o eliminar.</p>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-xl border border-brand-surface-2 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-brand-ink">Marcas</h2>
            <button
              disabled={!isSuperAdmin}
              onClick={() => {
                const nombre = window.prompt("Nueva marca:");
                if (nombre?.trim()) createMarcaMut.mutate(nombre.trim());
              }}
              className="rounded bg-brand-accent px-2 py-1 text-xs font-semibold text-black disabled:opacity-50"
            >
              + Agregar
            </button>
          </div>
          <ul className="space-y-1 text-sm">
            {marcasQ.data?.map((m) => (
              <li key={m.id} className="flex items-center justify-between rounded border border-brand-surface-2 px-2 py-1">
                <button
                  onClick={() => {
                    setMarcaId(m.id);
                    setModeloId("");
                  }}
                  className={`text-left ${marcaId === m.id ? "font-semibold text-brand-ink" : "text-brand-muted"}`}
                >
                  {m.nombre}
                </button>
                <div className="flex gap-1">
                  <button
                    disabled={!isSuperAdmin}
                    onClick={() => {
                      const nuevo = window.prompt("Renombrar marca:", m.nombre);
                      if (nuevo?.trim()) updateVehiculoMarca(m.id, nuevo.trim()).then(invalidate);
                    }}
                    className="text-xs text-brand-muted hover:underline disabled:opacity-40 disabled:no-underline"
                  >
                    Editar
                  </button>
                  <button
                    disabled={!isSuperAdmin}
                    onClick={() => {
                      if (window.confirm(`Eliminar marca ${m.nombre} y sus dependencias?`)) {
                        deleteVehiculoMarca(m.id).then(() => {
                          if (marcaId === m.id) {
                            setMarcaId("");
                            setModeloId("");
                          }
                          invalidate();
                        });
                      }
                    }}
                    className="text-xs text-red-600 hover:underline disabled:opacity-40 disabled:no-underline"
                  >
                    Eliminar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-brand-surface-2 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-brand-ink">Modelos</h2>
            <button
              disabled={!isSuperAdmin || marcaId === ""}
              onClick={() => {
                if (marcaId === "") return;
                const nombre = window.prompt(`Nuevo modelo para ${selectedMarca?.nombre}:`);
                if (nombre?.trim()) createModeloMut.mutate({ mid: Number(marcaId), nombre: nombre.trim() });
              }}
              className="rounded bg-brand-accent px-2 py-1 text-xs font-semibold text-black disabled:opacity-50"
            >
              + Agregar
            </button>
          </div>
          <ul className="space-y-1 text-sm">
            {modelosQ.data?.map((m) => (
              <li key={m.id} className="flex items-center justify-between rounded border border-brand-surface-2 px-2 py-1">
                <button
                  onClick={() => setModeloId(m.id)}
                  className={`text-left ${modeloId === m.id ? "font-semibold text-brand-ink" : "text-brand-muted"}`}
                >
                  {m.nombre}
                </button>
                <div className="flex gap-1">
                  <button
                    disabled={!isSuperAdmin}
                    onClick={() => {
                      const nuevo = window.prompt("Renombrar modelo:", m.nombre);
                      if (nuevo?.trim()) updateVehiculoModelo(m.id, m.marca_id, nuevo.trim()).then(invalidate);
                    }}
                    className="text-xs text-brand-muted hover:underline disabled:opacity-40 disabled:no-underline"
                  >
                    Editar
                  </button>
                  <button
                    disabled={!isSuperAdmin}
                    onClick={() => {
                      if (window.confirm(`Eliminar modelo ${m.nombre} y sus versiones?`)) {
                        deleteVehiculoModelo(m.id).then(() => {
                          if (modeloId === m.id) setModeloId("");
                          invalidate();
                        });
                      }
                    }}
                    className="text-xs text-red-600 hover:underline disabled:opacity-40 disabled:no-underline"
                  >
                    Eliminar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-brand-surface-2 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-brand-ink">Versiones</h2>
            <button
              disabled={!isSuperAdmin || modeloId === ""}
              onClick={() => {
                if (modeloId === "") return;
                const nombre = window.prompt(`Nueva versión para ${selectedModelo?.nombre}:`);
                if (nombre?.trim()) createVersionMut.mutate({ mid: Number(modeloId), nombre: nombre.trim() });
              }}
              className="rounded bg-brand-accent px-2 py-1 text-xs font-semibold text-black disabled:opacity-50"
            >
              + Agregar
            </button>
          </div>
          <ul className="space-y-1 text-sm">
            {versionesQ.data?.map((v) => (
              <li key={v.id} className="flex items-center justify-between rounded border border-brand-surface-2 px-2 py-1">
                <span className="text-brand-ink">{v.nombre}</span>
                <div className="flex gap-1">
                  <button
                    disabled={!isSuperAdmin}
                    onClick={() => {
                      const nuevo = window.prompt("Renombrar versión:", v.nombre);
                      if (nuevo?.trim()) updateVehiculoVersion(v.id, v.modelo_id, nuevo.trim()).then(invalidate);
                    }}
                    className="text-xs text-brand-muted hover:underline disabled:opacity-40 disabled:no-underline"
                  >
                    Editar
                  </button>
                  <button
                    disabled={!isSuperAdmin}
                    onClick={() => {
                      if (window.confirm(`Eliminar versión ${v.nombre}?`)) {
                        deleteVehiculoVersion(v.id).then(invalidate);
                      }
                    }}
                    className="text-xs text-red-600 hover:underline disabled:opacity-40 disabled:no-underline"
                  >
                    Eliminar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

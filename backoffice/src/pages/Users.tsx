import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import {
  createUser,
  getCurrentTenant,
  listRoles,
  listSucursales,
  listUsers,
  resetUserPassword,
  updateTenantQuota,
  updateUser,
} from "@/services/users";
import type { User, UserCreateInput } from "@/types";

type FormState = {
  id: number | null;
  nombre: string;
  email: string;
  role_id: number | "";
  sucursal_id: number | "";
  telefono: string;
};

const emptyForm: FormState = {
  id: null,
  nombre: "",
  email: "",
  role_id: "",
  sucursal_id: "",
  telefono: "",
};

export default function Users() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const isSuperAdmin = user?.role_code === "SuperAdmin";

  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const rolesQ = useQuery({ queryKey: ["roles"], queryFn: listRoles });
  const sucursalesQ = useQuery({ queryKey: ["sucursales"], queryFn: listSucursales });
  const tenantQ = useQuery({ queryKey: ["tenant-current"], queryFn: getCurrentTenant });

  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["users"] });
    qc.invalidateQueries({ queryKey: ["tenant-current"] });
  };

  const saveMut = useMutation({
    mutationFn: async (f: FormState) => {
      const payload: UserCreateInput = {
        nombre: f.nombre.trim(),
        email: f.email.trim(),
        role_id: Number(f.role_id),
        sucursal_id: f.sucursal_id === "" ? null : Number(f.sucursal_id),
        telefono: f.telefono.trim() || null,
      };
      if (f.id === null) return createUser(payload);
      return updateUser(f.id, payload);
    },
    onSuccess: () => {
      invalidate();
      setForm(null);
      setError(null);
    },
    onError: (e: unknown) => setError(extractError(e)),
  });

  const toggleActiveMut = useMutation({
    mutationFn: (u: User) => updateUser(u.id, { activo: !u.activo }),
    onSuccess: invalidate,
    onError: (e: unknown) => alert(extractError(e)),
  });

  const resetMut = useMutation({
    mutationFn: (u: User) => resetUserPassword(u.id),
    onSuccess: () => alert("Contraseña restablecida a admin123."),
    onError: (e: unknown) => alert(extractError(e)),
  });

  const quotaMut = useMutation({
    mutationFn: (max: number | null) => updateTenantQuota(tenantQ.data!.id, max),
    onSuccess: invalidate,
    onError: (e: unknown) => alert(extractError(e)),
  });

  const tenant = tenantQ.data;
  const quotaLabel = useMemo(() => {
    if (!tenant) return "";
    const limite = tenant.max_usuarios === null ? "Ilimitado" : tenant.max_usuarios;
    return `${tenant.usuarios_activos} / ${limite}`;
  }, [tenant]);

  const atLimit =
    tenant?.max_usuarios != null && tenant.usuarios_activos >= tenant.max_usuarios;

  function handleEditQuota() {
    if (!tenant) return;
    const input = window.prompt(
      "Cupo de usuarios (número, o vacío para ilimitado):",
      tenant.max_usuarios === null ? "" : String(tenant.max_usuarios),
    );
    if (input === null) return;
    const trimmed = input.trim();
    quotaMut.mutate(trimmed === "" ? null : Math.max(0, parseInt(trimmed, 10) || 0));
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-ink">Gestión de Usuarios</h1>
          <p className="text-sm text-brand-muted">{tenant?.nombre}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-white px-4 py-2 text-sm shadow-sm">
            <span className="text-brand-muted">Cupo: </span>
            <span className={`font-semibold ${atLimit ? "text-red-600" : "text-brand-ink"}`}>
              {quotaLabel}
            </span>
            {isSuperAdmin && (
              <button
                onClick={handleEditQuota}
                className="ml-2 text-xs text-brand-accent-600 hover:underline"
              >
                editar
              </button>
            )}
          </div>
          <button
            onClick={() => {
              setError(null);
              setForm({ ...emptyForm });
            }}
            className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600"
          >
            + Nuevo usuario
          </button>
        </div>
      </div>

      {usersQ.isLoading && <p className="text-brand-muted">Cargando usuarios…</p>}
      {usersQ.isError && <p className="text-red-600">No se pudieron cargar los usuarios.</p>}

      {usersQ.data && (
        <div className="overflow-x-auto rounded-xl border border-brand-surface-2 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-surface-2 text-left text-brand-muted">
                <th className="px-4 py-3 font-medium">Nombre</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Rol</th>
                <th className="px-4 py-3 font-medium">Sucursal</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usersQ.data.map((u) => (
                <tr key={u.id} className="border-b border-brand-surface-2 last:border-0">
                  <td className="px-4 py-3 font-medium text-brand-ink">{u.nombre}</td>
                  <td className="px-4 py-3 text-brand-muted">{u.email}</td>
                  <td className="px-4 py-3">{u.role}</td>
                  <td className="px-4 py-3 text-brand-muted">{u.sucursal ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        u.activo ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-500"
                      }`}
                    >
                      {u.activo ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2 text-xs">
                      <button
                        onClick={() =>
                          setForm({
                            id: u.id,
                            nombre: u.nombre,
                            email: u.email,
                            role_id: u.role_id,
                            sucursal_id: u.sucursal_id ?? "",
                            telefono: u.telefono ?? "",
                          })
                        }
                        className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => toggleActiveMut.mutate(u)}
                        className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface"
                      >
                        {u.activo ? "Desactivar" : "Activar"}
                      </button>
                      <button
                        onClick={() => resetMut.mutate(u)}
                        className="rounded border border-brand-surface-2 px-2 py-1 hover:bg-brand-surface"
                      >
                        Reset clave
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {form && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90dvh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold text-brand-ink">
              {form.id === null ? "Nuevo usuario" : "Editar usuario"}
            </h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                saveMut.mutate(form);
              }}
              className="space-y-3"
            >
              <Field label="Nombre">
                <input
                  required
                  value={form.nombre}
                  onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                  className={inputCls}
                />
              </Field>
              <Field label="Email">
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className={inputCls}
                />
              </Field>
              <Field label="Rol">
                <select
                  required
                  value={form.role_id}
                  onChange={(e) => setForm({ ...form, role_id: Number(e.target.value) })}
                  className={inputCls}
                >
                  <option value="" disabled>
                    Seleccionar rol
                  </option>
                  {rolesQ.data?.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.nombre}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Sucursal (opcional)">
                <select
                  value={form.sucursal_id}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      sucursal_id: e.target.value === "" ? "" : Number(e.target.value),
                    })
                  }
                  className={inputCls}
                >
                  <option value="">Sin sucursal</option>
                  {sucursalesQ.data?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nombre}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Teléfono (opcional)">
                <input
                  value={form.telefono}
                  onChange={(e) => setForm({ ...form, telefono: e.target.value })}
                  className={inputCls}
                />
              </Field>

              {form.id === null && (
                <p className="text-xs text-brand-muted">
                  La contraseña inicial será <code>admin123</code>.
                </p>
              )}
              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="mt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setForm(null)}
                  className="rounded-lg border border-brand-surface-2 px-4 py-2 text-sm hover:bg-brand-surface"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saveMut.isPending}
                  className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-black hover:bg-brand-accent-600 disabled:opacity-60"
                >
                  {saveMut.isPending ? "Guardando…" : "Guardar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-brand-surface-2 px-3 py-2 text-sm outline-none focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-brand-ink">{label}</span>
      {children}
    </label>
  );
}

function extractError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "Ocurrió un error. Intenta nuevamente.";
}

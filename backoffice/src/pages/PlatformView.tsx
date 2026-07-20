import { Navigate, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listTenants } from "@/services/auth";
import { useAuth } from "@/context/AuthContext";

export default function PlatformView() {
  const { user, isSuperAdmin, selectTenant, logout } = useAuth();
  const navigate = useNavigate();
  const [entering, setEntering] = useState<number | null>(null);
  const { data: tenants, isLoading, isError } = useQuery({
    queryKey: ["tenants"],
    queryFn: listTenants,
    enabled: isSuperAdmin,
  });

  // Solo el SuperAdmin accede a la vista de plataforma (guard tras los hooks).
  if (!isSuperAdmin) return <Navigate to="/" replace />;

  async function handleEnter(tenantId: number) {
    setEntering(tenantId);
    try {
      await selectTenant(tenantId);
      navigate("/", { replace: true });
    } finally {
      setEntering(null);
    }
  }

  return (
    <div className="min-h-screen bg-brand-dark px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-accent font-bold text-black">
              EC
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Panel de Plataforma</h1>
              <p className="text-sm text-brand-muted-2">
                Hola {user?.nombre?.split(" ")[0]}, elige una automotora para trabajar
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="rounded-lg border border-brand-dark-700 px-3 py-1.5 text-xs text-brand-surface-2 hover:bg-brand-dark-700"
          >
            Cerrar sesión
          </button>
        </div>

        {isLoading && <p className="text-brand-muted-2">Cargando automotoras…</p>}
        {isError && <p className="text-red-400">No se pudo cargar el directorio de tenants.</p>}

        <div className="grid gap-3 sm:grid-cols-2">
          {tenants?.map((t) => (
            <div
              key={t.id}
              className="flex flex-col justify-between rounded-xl bg-white p-5 shadow"
            >
              <div>
                <p className="font-semibold text-brand-ink">{t.nombre}</p>
                <p className="text-sm text-brand-muted">{t.dominio}</p>
                <span
                  className={`mt-2 inline-block rounded-full px-2 py-0.5 text-xs ${
                    t.activo ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {t.activo ? "Activo" : "Inactivo"}
                </span>
              </div>
              <button
                disabled={!t.activo || entering === t.id}
                onClick={() => handleEnter(t.id)}
                className="mt-4 rounded-lg bg-brand-accent py-2 text-sm font-semibold text-black transition hover:bg-brand-accent-600 disabled:opacity-60"
              >
                {entering === t.id ? "Entrando…" : "Entrar"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

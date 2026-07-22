import { NavLink } from "react-router-dom";
import { useNavigationMenu } from "@/hooks/useNavigationMenu";
import { useAuth } from "@/context/AuthContext";
import TenantSwitcher from "@/components/TenantSwitcher";

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const { data, isLoading, isError } = useNavigationMenu();

  return (
    <aside className="flex h-screen w-64 flex-col bg-brand-dark pt-safe text-white">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-accent font-bold text-black">
          EC
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight">EffiCarBroker</p>
          <p className="text-xs text-brand-muted-2">{user?.tenant ?? "Plataforma"}</p>
        </div>
      </div>

      <TenantSwitcher />

      <nav className="flex-1 overflow-y-auto px-3 pb-4">
        {isLoading && <p className="px-2 py-2 text-xs text-brand-muted-2">Cargando menú…</p>}
        {isError && <p className="px-2 py-2 text-xs text-red-400">No se pudo cargar el menú</p>}
        {data?.sections.map((section) => (
          <div key={section.code} className="mb-4">
            <p className="px-2 py-1 text-xs font-semibold uppercase tracking-wide text-brand-muted-2">
              {section.label}
            </p>
            <ul className="mt-1 space-y-0.5">
              {section.items.map((item) => (
                <li key={item.code}>
                  <NavLink
                    to={item.ruta}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      `block rounded-lg px-3 py-2.5 text-sm transition ${
                        isActive
                          ? "bg-brand-accent font-medium text-black"
                          : "text-brand-surface-2 hover:bg-brand-dark-700"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-brand-dark-700 px-4 py-3">
        <p className="truncate text-sm font-medium">{user?.nombre}</p>
        <p className="truncate text-xs text-brand-muted-2">{user?.role}</p>
        <button
          onClick={logout}
          className="mt-2 w-full rounded-lg border border-brand-dark-700 py-1.5 text-xs text-brand-surface-2 transition hover:bg-brand-dark-700"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}

import { Outlet } from "react-router-dom";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Overlay para cerrar el drawer en móvil */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar: drawer off-canvas en móvil, estático en md+ */}
      <div
        className={`fixed inset-y-0 left-0 z-40 transition-transform duration-200 md:static md:z-auto md:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar onNavigate={() => setMobileOpen(false)} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header móvil con botón de menú (oculto en md+) */}
        <header className="flex items-center gap-3 border-b border-brand-surface-2 bg-white px-4 py-3 pt-safe md:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            aria-label="Abrir menú"
            className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-brand-ink transition hover:bg-brand-surface-2"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-accent text-sm font-bold text-black">
              EC
            </div>
            <span className="text-sm font-semibold text-brand-ink">EffiCarBroker</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-brand-surface p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

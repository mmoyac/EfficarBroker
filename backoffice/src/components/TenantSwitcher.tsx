import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

/** Visible solo para SuperAdmin: muestra el tenant activo y permite cambiarlo. */
export default function TenantSwitcher() {
  const { isSuperAdmin, user, exitTenant } = useAuth();
  const navigate = useNavigate();
  const [switching, setSwitching] = useState(false);

  if (!isSuperAdmin || !user?.active_tenant) return null;

  async function handleChange() {
    setSwitching(true);
    try {
      await exitTenant();
      navigate("/plataforma", { replace: true });
    } finally {
      setSwitching(false);
    }
  }

  return (
    <div className="mx-3 mb-3 rounded-lg bg-brand-dark-700/60 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-brand-muted-2">Operando como</p>
      <p className="truncate text-sm font-medium text-white">{user.active_tenant}</p>
      <button
        onClick={handleChange}
        disabled={switching}
        className="mt-1 text-xs text-brand-accent hover:underline disabled:opacity-60"
      >
        {switching ? "Cambiando…" : "Cambiar automotora"}
      </button>
    </div>
  );
}

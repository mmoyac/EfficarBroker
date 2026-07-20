import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "@/context/AuthContext";

/** Fuerza al SuperAdmin sin tenant activo a la vista de plataforma. */
export default function TenantGate({ children }: { children: ReactNode }) {
  const { needsTenantSelection } = useAuth();
  if (needsTenantSelection) {
    return <Navigate to="/plataforma" replace />;
  }
  return <>{children}</>;
}

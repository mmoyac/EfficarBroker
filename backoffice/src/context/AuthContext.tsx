import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  exitTenant as exitTenantRequest,
  getMe,
  login as loginRequest,
  logout as logoutRequest,
  selectTenant as selectTenantRequest,
} from "@/services/auth";
import { tokenStore } from "@/services/api";
import type { UserMe } from "@/types";

interface AuthContextValue {
  user: UserMe | null;
  loading: boolean;
  isSuperAdmin: boolean;
  /** SuperAdmin autenticado que aún no ha elegido un tenant activo. */
  needsTenantSelection: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  selectTenant: (tenantId: number) => Promise<void>;
  exitTenant: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();

  // Rehidrata la sesión si hay un token guardado.
  useEffect(() => {
    if (!tokenStore.getAccess()) {
      setLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => {
    const isSuperAdmin = user?.role_code === "SuperAdmin";
    return {
      user,
      loading,
      isSuperAdmin,
      needsTenantSelection: Boolean(isSuperAdmin && !user?.active_tenant_id),
      login: async (email, password) => {
        const me = await loginRequest(email, password);
        setUser(me);
      },
      logout: () => {
        logoutRequest();
        setUser(null);
        queryClient.clear();
      },
      selectTenant: async (tenantId) => {
        await selectTenantRequest(tenantId);
        await queryClient.invalidateQueries();
        setUser(await getMe());
      },
      exitTenant: async () => {
        await exitTenantRequest();
        await queryClient.invalidateQueries();
        setUser(await getMe());
      },
    };
  }, [user, loading, queryClient]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}

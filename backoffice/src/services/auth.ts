import { api, tokenStore } from "@/services/api";
import type { AccessToken, NavigationMenu, Tenant, TokenPair, UserMe } from "@/types";

export async function login(email: string, password: string): Promise<UserMe> {
  const { data } = await api.post<TokenPair>("/auth/login", { email, password });
  tokenStore.set(data.access_token, data.refresh_token);
  return getMe();
}

export async function getMe(): Promise<UserMe> {
  const { data } = await api.get<UserMe>("/auth/me");
  return data;
}

export async function getNavigationMenu(): Promise<NavigationMenu> {
  const { data } = await api.get<NavigationMenu>("/navigation/menu");
  return data;
}

export async function listTenants(): Promise<Tenant[]> {
  const { data } = await api.get<Tenant[]>("/tenants");
  return data;
}

export async function selectTenant(tenantId: number): Promise<void> {
  const { data } = await api.post<AccessToken>("/auth/select-tenant", { tenant_id: tenantId });
  tokenStore.set(data.access_token); // conserva el refresh token existente
}

export async function exitTenant(): Promise<void> {
  const { data } = await api.post<AccessToken>("/auth/exit-tenant", {});
  tokenStore.set(data.access_token);
}

export function logout(): void {
  tokenStore.clear();
}

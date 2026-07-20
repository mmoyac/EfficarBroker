import { api } from "@/services/api";
import type {
  Role,
  Sucursal,
  Tenant,
  User,
  UserCreateInput,
  UserUpdateInput,
} from "@/types";

export async function listUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>("/users");
  return data;
}

export async function createUser(input: UserCreateInput): Promise<User> {
  const { data } = await api.post<User>("/users", input);
  return data;
}

export async function updateUser(id: number, input: UserUpdateInput): Promise<User> {
  const { data } = await api.patch<User>(`/users/${id}`, input);
  return data;
}

export async function resetUserPassword(id: number): Promise<void> {
  await api.post(`/users/${id}/reset-password`, {});
}

export async function listRoles(): Promise<Role[]> {
  const { data } = await api.get<Role[]>("/roles");
  return data;
}

export async function listSucursales(): Promise<Sucursal[]> {
  const { data } = await api.get<Sucursal[]>("/sucursales");
  return data;
}

export async function getCurrentTenant(): Promise<Tenant> {
  const { data } = await api.get<Tenant>("/tenants/current");
  return data;
}

export async function updateTenantQuota(
  tenantId: number,
  maxUsuarios: number | null,
): Promise<Tenant> {
  const { data } = await api.patch<Tenant>(`/tenants/${tenantId}`, { max_usuarios: maxUsuarios });
  return data;
}

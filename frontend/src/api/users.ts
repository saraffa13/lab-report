import { apiClient } from "./client";

export type Role = { id: number; code: string; name: string; description: string };

export type LabUser = {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  designation: string;
  qualification: string;
  role: number | null;
  role_code: string | null;
  role_name: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  phone_verified: boolean;
  email_verified: boolean;
  created_at: string;
};

type Paginated<T> = { results: T[] } | T[];
const unwrap = <T,>(p: Paginated<T>): T[] => (Array.isArray(p) ? p : p.results);

export async function listUsers(): Promise<LabUser[]> {
  const { data } = await apiClient.get<Paginated<LabUser>>("/v1/users/");
  return unwrap(data);
}

export async function createUser(body: Partial<LabUser> & { password?: string }): Promise<LabUser> {
  const { data } = await apiClient.post<LabUser>("/v1/users/", body);
  return data;
}

export async function updateUser(id: string, body: Partial<LabUser> & { password?: string }): Promise<LabUser> {
  const { data } = await apiClient.patch<LabUser>(`/v1/users/${id}/`, body);
  return data;
}

export async function listRoles(): Promise<Role[]> {
  const { data } = await apiClient.get<Paginated<Role>>("/v1/roles/");
  return unwrap(data);
}

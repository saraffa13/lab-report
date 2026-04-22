import { apiClient } from "./client";

export type LabSummary = {
  id: string;
  name: string;
  slug: string;
  city: string;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  designation: string;
  qualification: string;
  lab: LabSummary | null;
  role_code: string | null;
  is_superuser: boolean;
};

export type LoginResponse = {
  access: string;
  refresh: string;
  user: User;
};

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/v1/auth/login/", { email, password });
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/v1/auth/me/");
  return data;
}

const ACCESS_KEY = "labreport.access_token";
const REFRESH_KEY = "labreport.refresh_token";
const USER_KEY = "labreport.user";

export function storeSession(resp: LoginResponse) {
  localStorage.setItem(ACCESS_KEY, resp.access);
  localStorage.setItem(REFRESH_KEY, resp.refresh);
  localStorage.setItem(USER_KEY, JSON.stringify(resp.user));
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function cachedUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function hasSession(): boolean {
  return !!localStorage.getItem(ACCESS_KEY);
}

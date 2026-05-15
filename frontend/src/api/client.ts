import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

const ACCESS_KEY = "labreport.access_token";
const REFRESH_KEY = "labreport.refresh_token";
const USER_KEY = "labreport.user";

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  withCredentials: true,
});

apiClient.interceptors.request.use((config: any) => {
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function clearAndRedirect() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) throw new Error("no refresh token");
  // Bare axios (not apiClient) to avoid recursing through our interceptor.
  const { data } = await axios.post<{ access: string; refresh?: string }>(
    `${baseURL}/v1/auth/refresh/`,
    { refresh },
    { timeout: 30000 },
  );
  localStorage.setItem(ACCESS_KEY, data.access);
  if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
  return data.access;
}

apiClient.interceptors.response.use(
  (response: any) => response,
  async (error: any) => {
    const status = error?.response?.status;
    const original = error?.config as (any & { _retried?: boolean }) | undefined;
    const url = (original?.url ?? "") as string;

    // Don't try to refresh for the login/refresh endpoints themselves.
    const isAuthEndpoint =
      url.includes("/v1/auth/login") || url.includes("/v1/auth/refresh");

    if (status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccess = await refreshPromise;
        original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${newAccess}` };
        return apiClient(original);
      } catch {
        clearAndRedirect();
        return Promise.reject(error);
      }
    }

    if (status === 401 && !isAuthEndpoint) {
      clearAndRedirect();
    }
    return Promise.reject(error);
  },
);

import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("labreport.access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // If our session went bad, bounce to login.
    if (error?.response?.status === 401 && window.location.pathname !== "/login") {
      localStorage.removeItem("labreport.access_token");
      localStorage.removeItem("labreport.refresh_token");
      localStorage.removeItem("labreport.user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

import axios from "axios";

const BASE = import.meta.env.BASE_URL; // e.g. "/webui/" or "/"

export const api = axios.create({
  baseURL: BASE + "api",
  withCredentials: true,
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.endsWith("/login")) {
      window.location.href = BASE + "login";
    }
    return Promise.reject(err);
  }
);

export interface PreflightCheck {
  name: string;
  status: "ok" | "warn" | "fail";
  message: string;
  details?: string;
}

export interface PreflightResult {
  status: "ok" | "warn" | "fail";
  message: string;
  details?: string;
  checks: PreflightCheck[];
}

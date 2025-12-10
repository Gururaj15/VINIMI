// src/lib/api.ts
import { getManager } from "@/lib/auth";
export const API_BASE =
  (import.meta as any).env?.VITE_API_BASE ||
  (import.meta as any).env?.VITE_API_URL ||
  "http://localhost:8001";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  parseJson = true,
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (!headers["Content-Type"] && options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  // no auth headers needed for simple demo

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const parsed = text ? JSON.parse(text) : null;
      const detail =
        (parsed && typeof parsed === "object" && (parsed.detail || parsed.message)) || text;
      throw new Error(detail || `HTTP ${res.status}`);
    } catch {
      throw new Error(text || `HTTP ${res.status} ${res.statusText}`);
    }
  }
  if (!parseJson) {
    return (await res.text()) as T;
  }
  return (await res.json()) as T;
}

async function get<T>(path: string): Promise<T> {
  return apiFetch<T>(path);
}

/** Shapes returned by FastAPI /api/workers */
export type WorkerImage = {
  id: number;
  url: string;
  captured_at: string;
  helmet_on: boolean;
  type?: string;
};

export type WorkerViolation = {
  id: number;
  timestamp: string;
  location_name?: string;
  reason: string;
  severity: "low" | "medium" | "high";
  image_url?: string;
};

export interface WorkerApi {
  id: number;
  name: string;
  phone: string;
  company_id: number;
  location_id: number;
  joined_at: string;
  company_name: string;
  location_name: string;
  images?: WorkerImage[];
  violations?: WorkerViolation[];
   violation_count?: number;
}

export async function fetchWorkers(): Promise<WorkerApi[]> {
  return get<WorkerApi[]>("/api/workers");
}

export async function fetchWorker(workerId: number): Promise<WorkerApi> {
  return get<WorkerApi>(`/api/workers/${workerId}`);
}

export async function fetchWorkerMedia(workerId: number): Promise<WorkerImage[]> {
  return get<WorkerImage[]>(`/api/workers/${workerId}/media`);
}

export async function fetchWorkerViolations(workerId: number): Promise<WorkerViolation[]> {
  const raw = await get<any[]>(`/api/workers/${workerId}/violations`);
  return raw.map((r) => ({
    id: r.id ?? r.violation_id ?? Math.random(),
    timestamp: r.timestamp ?? r.detected_at ?? "",
    location_name:
      r.location_name ?? r.location ?? r.details?.location_name ?? undefined,
    reason:
      r.reason ??
      r.details?.reason ??
      (r.sms_status === "helmet_off" ? "Helmet Off" : "Safety Violation"),
    severity:
      (r.severity as any) ||
      (r.details?.severity as any) ||
      (r.sms_status === "helmet_off" ? "high" : "medium"),
    image_url:
      r.image_url ??
      r.frame_path ??
      (r.details?.frame_url as string | undefined) ??
      undefined,
  })) as WorkerViolation[];
}

export type CameraStatus = "online" | "offline" | "error" | "pending";

export interface Camera {
  id: number;
  name: string;
  company_id: number;
  location_id: number;
  status: CameraStatus;
}

export async function fetchCameras(companyId: number): Promise<Camera[]> {
  return apiFetch<Camera[]>(`/api/cameras?company_id=${companyId}`);
}

export interface SmsTestResponse {
  status: string;
  sid?: string | null;
}

export interface RecentAlert {
  id: number | string;
  timestamp?: string | null;
  worker_name: string;
  worker_id?: number | null;
  location_name?: string | null;
  location_id?: number | null;
  phone?: string | null;
  sms_status?: string | null;
  sms_sid?: string | null;
  frame_path?: string | null;
  details?: Record<string, unknown> | null;
}

export async function fetchRecentAlerts(limit = 20): Promise<RecentAlert[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiFetch<RecentAlert[]>(`/api/live/recent-alerts?${params.toString()}`);
}

export async function fetchViolations(limit = 200): Promise<RecentAlert[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiFetch<RecentAlert[]>(`/api/violations?${params.toString()}`);
}

export async function sendTestAlertSms(
  phone: string,
  message: string,
  workerId?: number,
  workerName?: string,
): Promise<SmsTestResponse> {
  return apiFetch<SmsTestResponse>("/api/alerts/test", {
    method: "POST",
    body: JSON.stringify({
      phone,
      message,
      worker_id: workerId,
      worker_name: workerName,
    }),
  });
}

export interface AuthResponse {
  status?: string;
  manager: { id: number; name: string; email?: string; company_id: number };
}

export async function loginManager(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, username: email }),
  });
}

export async function signupManager(payload: {
  name: string;
  email: string;
  password: string;
  companyName: string;
}): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// plain manager APIs
export interface ManagerPayload {
  name: string;
  email: string;
  password: string;
  company_id: number;
}

export async function managerSignup(payload: ManagerPayload) {
  return apiFetch("/api/manager/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function managerLogin(payload: { email: string; password: string }) {
  return apiFetch("/api/manager/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function managerGet(id: number) {
  return apiFetch(`/api/manager/${id}`);
}

export async function managerUpdate(
  id: number,
  payload: { name?: string; company_id?: number; password?: string }
) {
  return apiFetch(`/api/manager/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

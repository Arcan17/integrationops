// Lightweight API client for the IntegrationOps dashboard.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const TOKEN_KEY = "io_token";

// ---- Token management (browser only) -------------------------------------

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ---- Auth ------------------------------------------------------------------

export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Incorrect email or password");
  const data = (await res.json()) as { access_token: string };
  setToken(data.access_token);
}

// ---- Generic GET -----------------------------------------------------------

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return (await res.json()) as T;
}

// ---- Authenticated file download ------------------------------------------

export async function downloadExport(id: number, filename: string): Promise<void> {
  const res = await fetch(`${API_URL}/exports/${id}/download`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ---- API types -------------------------------------------------------------

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: "admin" | "operator" | "viewer";
  is_active: boolean;
  created_at: string;
}

export interface UploadedFile {
  id: number;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  row_count: number;
  status: string;
}

export interface UploadBatch {
  id: number;
  created_by: number | null;
  status: string;
  total_files: number;
  created_at: string;
  files?: UploadedFile[];
}

export interface ValidationError {
  id: number;
  uploaded_file_id: number;
  row_number: number | null;
  column_name: string | null;
  error_code: string;
  message: string;
}

export interface Job {
  id: number;
  created_by: number | null;
  batch_id: number | null;
  job_type: string;
  status: string;
  attempts: number;
  max_attempts: number;
  task_id: string | null;
  last_error: string | null;
  result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ExportJob {
  id: number;
  batch_id: number | null;
  requested_by: number | null;
  export_format: string;
  status: string;
  file_path: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  actor_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

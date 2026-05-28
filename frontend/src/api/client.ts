import {
  AuthResponse,
  BatchJobCreateResponse,
  DashboardStatsResponse,
  HistoryRecordResponse,
  InsightResponse,
  JobCreateResponse,
  JobProgressResponse,
  SummaryLength,
  SummaryMode,
  SummaryResponse,
  SummarySource,
  UserResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_STORAGE_KEY = "alignpdf-auth-token";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    throw new Error(payload.detail ?? "Request failed.");
  }
  return response.json() as Promise<T>;
}

export function getAuthToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAuthToken(token: string | null): void {
  if (!token) {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(): Promise<UserResponse> {
  return apiRequest<UserResponse>("/api/v1/auth/me");
}

export async function createJob(file: File): Promise<JobCreateResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<JobCreateResponse>("/api/v1/jobs", { method: "POST", body: formData });
}

export async function createBatchJobs(files: File[]): Promise<BatchJobCreateResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  return apiRequest<BatchJobCreateResponse>("/api/v1/jobs/batch", { method: "POST", body: formData });
}

export async function getJob(jobId: string): Promise<JobProgressResponse> {
  return apiRequest<JobProgressResponse>(`/api/v1/jobs/${jobId}`);
}

export async function retryJob(jobId: string): Promise<JobCreateResponse> {
  return apiRequest<JobCreateResponse>(`/api/v1/jobs/${jobId}/retry`, { method: "POST" });
}

export async function getHistory(): Promise<HistoryRecordResponse[]> {
  return apiRequest<HistoryRecordResponse[]>("/api/v1/history");
}

export async function getDashboard(): Promise<DashboardStatsResponse> {
  return apiRequest<DashboardStatsResponse>("/api/v1/dashboard");
}

export async function generateSummary(
  jobId: string,
  payload: { source_type: SummarySource; mode: SummaryMode; length: SummaryLength; language_hint?: string },
): Promise<SummaryResponse> {
  return apiRequest<SummaryResponse>(`/api/v1/jobs/${jobId}/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getInsights(jobId: string, sourceType: SummarySource): Promise<InsightResponse> {
  return apiRequest<InsightResponse>(`/api/v1/jobs/${jobId}/insights?source_type=${sourceType}`);
}

export async function downloadFile(path: string): Promise<void> {
  const headers = new Headers();
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Download failed." }));
    throw new Error(payload.detail ?? "Download failed.");
  }

  const blob = await response.blob();
  const header = response.headers.get("Content-Disposition") ?? "";
  const matched = /filename="?([^"]+)"?/i.exec(header);
  const filename = matched?.[1] ?? "converted.docx";

  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(objectUrl);
}

export async function downloadDocx(path: string): Promise<void> {
  await downloadFile(path);
}

export function buildAbsoluteAssetUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }
  return `${API_BASE_URL}${path}`;
}

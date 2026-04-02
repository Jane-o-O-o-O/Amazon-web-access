import axios from "axios";
import type {
  CreateTaskRequest,
  TaskProgress,
  TaskResult,
  ListingDraft,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL, timeout: 30000 });

// ─── Tasks ────────────────────────────────────────────────────────────────────

export async function createTask(req: CreateTaskRequest): Promise<{ taskId: string; status: string }> {
  const { data } = await api.post("/api/tasks/product-analysis", req);
  return data;
}

export async function getTaskStatus(taskId: string): Promise<TaskProgress> {
  const { data } = await api.get(`/api/tasks/${taskId}`);
  return data;
}

export async function getTaskResult(taskId: string): Promise<TaskResult> {
  const { data } = await api.get(`/api/tasks/${taskId}/result`);
  return data;
}

// ─── Listings ─────────────────────────────────────────────────────────────────

export async function regenerateListing(params: {
  productId: string;
  market?: string;
  tone?: string;
  keywordFocus?: string[];
  productSpecs?: object;
  competitorInsights?: object;
}): Promise<{ productId: string; listing: ListingDraft }> {
  const { data } = await api.post("/api/listings/regenerate", params);
  return data;
}

// ─── Export ───────────────────────────────────────────────────────────────────

export function getExportCsvUrl(taskId: string): string {
  return `${BASE_URL}/api/export/tasks/${taskId}/csv`;
}

export function getExportJsonUrl(taskId: string): string {
  return `${BASE_URL}/api/export/tasks/${taskId}/json`;
}

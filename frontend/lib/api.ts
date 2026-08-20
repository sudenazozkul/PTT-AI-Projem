import type {
  AnalysisResponse,
  Branch,
  BranchDetailResponse,
  ComparisonResponse,
  MetadataResponse,
  MethodologyResponse,
  OverviewFilters,
  OverviewResponse,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const english = typeof document !== "undefined" && document.documentElement.lang === "en";
    const detail = payload?.detail;
    const message = english && detail === "Şube veya seçilen dönem bulunamadı."
      ? "No branch or data was found for the selected period."
      : detail ?? (english ? "Unable to retrieve data." : "Veri alınamadı.");
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

function appendList(query: URLSearchParams, key: string, values?: string[]) {
  values?.forEach((value) => query.append(key, value));
}

function overviewQuery(filters: OverviewFilters = {}) {
  const query = new URLSearchParams();
  if (filters.startDate) query.set("start_date", filters.startDate);
  if (filters.endDate) query.set("end_date", filters.endDate);
  appendList(query, "provinces", filters.provinces);
  appendList(query, "branch_types", filters.branchTypes);
  appendList(query, "branch_codes", filters.branchCodes);
  return query;
}

export const api = {
  metadata: () => request<MetadataResponse>("/meta"),
  methodology: () => request<MethodologyResponse>("/methodology"),
  branches: () => request<Branch[]>("/branches"),
  overview: (filters: OverviewFilters = {}) => {
    const query = overviewQuery(filters);
    return request<OverviewResponse>(`/overview${query.size ? `?${query}` : ""}`);
  },
  branchDetail: (code: string, startDate?: string, endDate?: string) => {
    const query = new URLSearchParams();
    if (startDate) query.set("start_date", startDate);
    if (endDate) query.set("end_date", endDate);
    return request<BranchDetailResponse>(`/branches/${code}${query.size ? `?${query}` : ""}`);
  },
  comparison: (codes: string[], startDate?: string, endDate?: string) => {
    const query = new URLSearchParams();
    appendList(query, "branch_codes", codes);
    if (startDate) query.set("start_date", startDate);
    if (endDate) query.set("end_date", endDate);
    return request<ComparisonResponse>(`/comparison?${query}`);
  },
  analysis: (codes: string[] = [], startDate?: string, endDate?: string) => {
    const query = new URLSearchParams();
    appendList(query, "branch_codes", codes);
    if (startDate) query.set("start_date", startDate);
    if (endDate) query.set("end_date", endDate);
    return request<AnalysisResponse>(`/analysis${query.size ? `?${query}` : ""}`);
  },
};

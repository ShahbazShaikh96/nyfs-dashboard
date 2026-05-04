import type {
  FilterOptions,
  RestaurantHistoryResponse,
  RestaurantsResponse,
  SummaryResponse
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8080";

type QueryFilters = {
  borough: string[];
  cuisine: string[];
  grade: string[];
  risk: string[];
  criticalOnly: "all" | "critical" | "non_critical";
  search: string;
  startDate: string;
  endDate: string;
  limit: number;
  offset?: number;
};

function createQueryString(filters: QueryFilters): string {
  const params = new URLSearchParams();
  filters.borough.forEach((v) => params.append("borough", v));
  filters.cuisine.forEach((v) => params.append("cuisine", v));
  filters.grade.forEach((v) => params.append("grade", v));
  filters.risk.forEach((v) => params.append("risk", v));
  if (filters.criticalOnly === "critical") params.set("critical_only", "true");
  if (filters.criticalOnly === "non_critical") params.set("critical_only", "false");
  if (filters.search.trim()) params.set("search", filters.search.trim());
  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);
  params.set("limit", String(filters.limit));
  if (filters.offset) params.set("offset", String(filters.offset));
  return params.toString();
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const response = await fetch(`${API_BASE_URL}/api/v1/filters`);
  if (!response.ok) throw new Error("Failed to load filter options.");
  return response.json();
}

export async function fetchMetadata(): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE_URL}/api/v1/metadata`);
  if (!response.ok) throw new Error("Failed to load refresh metadata.");
  return response.json();
}

export async function fetchRestaurants(filters: QueryFilters): Promise<RestaurantsResponse> {
  const query = createQueryString(filters);
  const response = await fetch(`${API_BASE_URL}/api/v1/restaurants?${query}`);
  if (!response.ok) throw new Error("Failed to load restaurants.");
  return response.json();
}

export async function fetchSummary(filters: QueryFilters): Promise<SummaryResponse> {
  const query = createQueryString({ ...filters, offset: 0, limit: 12000 });
  const response = await fetch(`${API_BASE_URL}/api/v1/summary?${query}`);
  if (!response.ok) throw new Error("Failed to load summary.");
  return response.json();
}

export async function fetchRestaurantHistory(
  restaurantId: number
): Promise<RestaurantHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/restaurants/${restaurantId}/history`);
  if (!response.ok) throw new Error("Failed to load restaurant history.");
  return response.json();
}

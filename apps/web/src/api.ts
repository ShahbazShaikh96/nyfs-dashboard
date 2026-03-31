import type { FilterOptions, RestaurantsResponse } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8080";

type QueryFilters = {
  borough: string[];
  cuisine: string[];
  grade: string[];
  risk: string[];
  criticalOnly: "all" | "critical" | "non_critical";
  search: string;
  limit: number;
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
  params.set("limit", String(filters.limit));
  return params.toString();
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const response = await fetch(`${API_BASE_URL}/api/v1/filters`);
  if (!response.ok) throw new Error("Failed to load filter options.");
  return response.json();
}

export async function fetchRestaurants(filters: QueryFilters): Promise<RestaurantsResponse> {
  const query = createQueryString(filters);
  const response = await fetch(`${API_BASE_URL}/api/v1/restaurants?${query}`);
  if (!response.ok) throw new Error("Failed to load restaurants.");
  return response.json();
}

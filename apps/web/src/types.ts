export type Restaurant = {
  restaurant_id: number;
  restaurant_name: string;
  borough: string;
  cuisine_type: string;
  inspection_grade: string;
  inspection_score: number;
  risk_level: string;
  risk_score: number;
  has_critical_violations: boolean;
  critical_violations: number;
  latest_inspection_date: string | null;
  full_address: string;
  street_name: string;
  photo_url: string | null;
  latitude: number;
  longitude: number;
};

export type FilterOptions = {
  boroughs: string[];
  cuisines: string[];
  grades: string[];
  risk_levels: string[];
};

export type RestaurantsResponse = {
  total: number;
  offset: number;
  limit: number;
  applied_filters: Record<string, unknown>;
  restaurants: Restaurant[];
};

export type SummaryResponse = {
  borough_scores: { borough: string; avg_score: number }[];
  grade_distribution: { grade: string; count: number }[];
  top_cuisines_critical: { cuisine_type: string; critical_violations: number }[];
  monthly_trend: { month: string; avg_score: number; inspections: number }[];
};

export type RestaurantHistoryPoint = {
  inspection_date: string | null;
  inspection_score: number;
  inspection_grade: string;
  critical_violations: number;
  risk_level: string;
  risk_score: number;
  inspection_type: string | null;
  action: string | null;
  violations: string | null;
};

export type RestaurantHistoryResponse = {
  restaurant_id: number;
  restaurant_name: string;
  borough: string;
  cuisine_type: string;
  full_address: string;
  street_name: string;
  photo_url: string | null;
  photo_source_label: string | null;
  points: RestaurantHistoryPoint[];
};

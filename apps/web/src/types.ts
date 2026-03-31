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
  applied_filters: Record<string, unknown>;
  restaurants: Restaurant[];
};

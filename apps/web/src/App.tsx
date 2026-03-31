import { useEffect, useMemo, useState } from "react";
import { fetchFilterOptions, fetchRestaurants } from "./api";
import { FilterPanel, type AppliedFilters } from "./components/FilterPanel";
import { MapView } from "./components/MapView";
import type { FilterOptions, Restaurant } from "./types";

const defaultFilters: AppliedFilters = {
  borough: [],
  cuisine: [],
  grade: [],
  risk: [],
  criticalOnly: "all",
  search: "",
  limit: 5000
};

export default function App() {
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [appliedFilters, setAppliedFilters] = useState<AppliedFilters>(defaultFilters);
  const [totalRestaurants, setTotalRestaurants] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const result = await fetchFilterOptions();
        setOptions(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load filter options.");
      }
    })();
  }, []);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchRestaurants(appliedFilters);
        setRestaurants(result.restaurants);
        setTotalRestaurants(result.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load restaurants.");
      } finally {
        setLoading(false);
      }
    })();
  }, [appliedFilters]);

  const kpi = useMemo(() => {
    if (!restaurants.length) {
      return {
        avgScore: 0,
        highRisk: 0
      };
    }
    const avgScore = restaurants.reduce((sum, r) => sum + r.inspection_score, 0) / restaurants.length;
    const highRisk = restaurants.filter((r) => r.risk_level === "High").length;
    return {
      avgScore,
      highRisk
    };
  }, [restaurants]);

  return (
    <div className="layout">
      <header className="header">
        <h1>NYFS Intelligence Platform</h1>
        <p>Map-first NYC restaurant hygiene intelligence for public decision-making.</p>
      </header>

      <section className="kpi-grid">
        <article className="kpi-card">
          <h3>Restaurants in View</h3>
          <p>{totalRestaurants.toLocaleString()}</p>
        </article>
        <article className="kpi-card">
          <h3>Average Score</h3>
          <p>{kpi.avgScore.toFixed(1)}</p>
        </article>
        <article className="kpi-card">
          <h3>High Risk</h3>
          <p>{kpi.highRisk.toLocaleString()}</p>
        </article>
      </section>

      <main className="main-grid">
        <FilterPanel options={options} applied={appliedFilters} onApply={setAppliedFilters} />
        <div className="map-panel">
          {loading ? <div className="status">Loading map data...</div> : null}
          {error ? <div className="status error">{error}</div> : null}
          <MapView restaurants={restaurants} />
        </div>
      </main>
    </div>
  );
}

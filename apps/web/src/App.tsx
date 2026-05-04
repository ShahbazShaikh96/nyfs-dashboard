import { useEffect, useMemo, useState } from "react";
import {
  fetchFilterOptions,
  fetchMetadata,
  fetchRestaurantHistory,
  fetchRestaurants,
  fetchSummary
} from "./api";
import { FilterPanel, type AppliedFilters } from "./components/FilterPanel";
import { IntelligencePanel } from "./components/IntelligencePanel";
import { MapView } from "./components/MapView";
import { RestaurantDrawer } from "./components/RestaurantDrawer";
import type { FilterOptions, Restaurant, RestaurantHistoryResponse, SummaryResponse } from "./types";

const defaultFilters: AppliedFilters = {
  borough: [],
  cuisine: [],
  grade: [],
  risk: [],
  criticalOnly: "all",
  search: "",
  startDate: "",
  endDate: "",
  limit: 5000
};

function useIsMobile(breakpoint = 768): boolean {
  const [isMobile, setIsMobile] = useState<boolean>(() => window.innerWidth <= breakpoint);

  useEffect(() => {
    const mediaQuery = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const update = () => setIsMobile(mediaQuery.matches);
    update();
    mediaQuery.addEventListener("change", update);
    return () => mediaQuery.removeEventListener("change", update);
  }, [breakpoint]);

  return isMobile;
}

export default function App() {
  const isMobile = useIsMobile();
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [appliedFilters, setAppliedFilters] = useState<AppliedFilters>(defaultFilters);
  const [totalRestaurants, setTotalRestaurants] = useState(0);
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<number | null>(null);
  const [selectedHistory, setSelectedHistory] = useState<RestaurantHistoryResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshMeta, setRefreshMeta] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [filterResult, metadataResult] = await Promise.all([
          fetchFilterOptions(),
          fetchMetadata().catch(() => null)
        ]);
        setOptions(filterResult);
        setRefreshMeta(metadataResult);
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
        const mobileSafeLimit = isMobile ? 1200 : 5000;
        const requestFilters = {
          ...appliedFilters,
          limit: Math.min(appliedFilters.limit, mobileSafeLimit)
        };
        const [restaurantResult, summaryResult] = await Promise.all([
          fetchRestaurants(requestFilters),
          fetchSummary(requestFilters)
        ]);
        setRestaurants(restaurantResult.restaurants);
        setTotalRestaurants(restaurantResult.total);
        setSummary(summaryResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load restaurants.");
      } finally {
        setLoading(false);
      }
    })();
  }, [appliedFilters, isMobile]);

  useEffect(() => {
    if (!selectedRestaurantId) return;
    void (async () => {
      setDrawerOpen(true);
      setDrawerLoading(true);
      try {
        const history = await fetchRestaurantHistory(selectedRestaurantId);
        setSelectedHistory(history);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load restaurant details.");
      } finally {
        setDrawerLoading(false);
      }
    })();
  }, [selectedRestaurantId]);

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

  const renderedRestaurants = useMemo(() => {
    if (!isMobile) return restaurants;
    return restaurants.slice(0, 800);
  }, [restaurants, isMobile]);

  const refreshedAt = useMemo(() => {
    const raw = refreshMeta?.refreshed_at_utc;
    if (typeof raw !== "string" || !raw) return "Unknown";
    const parsed = new Date(raw);
    if (Number.isNaN(parsed.getTime())) return "Unknown";
    return parsed.toLocaleString();
  }, [refreshMeta]);

  const sourceLabel = useMemo(() => {
    const raw = refreshMeta?.source;
    if (typeof raw !== "string" || !raw) return "NYC Open Data";
    return raw.replace(/_/g, " ");
  }, [refreshMeta]);

  return (
    <div className="layout">
      <header className="header">
        <div className="header-tag">NYC Public Food Safety Intelligence</div>
        <h1>Find Safer Places to Eat Across New York City</h1>
        <p className="header-lead">
          This dashboard helps residents, tourists, and students quickly interpret NYC restaurant
          inspection data using a map-first experience. Use filters to compare boroughs, cuisine
          types, grades, and risk patterns before choosing where to eat.
        </p>
        <div className="header-chips">
          <span className="chip">Data source: NYC Open Data</span>
          <span className="chip">Last updated: {refreshedAt}</span>
          <span className="chip">Pipeline status: {sourceLabel}</span>
        </div>
        <p className="header-note">
          Dashboard risk level is an informational NYFS indicator derived from inspection history,
          not an official NYC grade label.
        </p>
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

      <main className="main-grid advanced">
        <FilterPanel options={options} applied={appliedFilters} onApply={setAppliedFilters} />
        <div className="map-panel">
          {loading ? <div className="status">Loading map data...</div> : null}
          {error ? <div className="status error">{error}</div> : null}
          {isMobile && restaurants.length > renderedRestaurants.length ? (
            <div className="status mobile-hint">
              Mobile performance mode: showing top {renderedRestaurants.length.toLocaleString()}{" "}
              restaurants. Refine filters to narrow further.
            </div>
          ) : null}
          <MapView
            restaurants={renderedRestaurants}
            selectedRestaurantId={selectedRestaurantId}
            onSelectRestaurant={setSelectedRestaurantId}
            mobileMode={isMobile}
          />
        </div>
        <IntelligencePanel summary={summary} />
      </main>

      <RestaurantDrawer
        history={selectedHistory}
        open={drawerOpen}
        loading={drawerLoading}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedRestaurantId(null);
        }}
      />
    </div>
  );
}

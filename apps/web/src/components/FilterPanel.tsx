import { useMemo, useState } from "react";
import type { FilterOptions } from "../types";

export type AppliedFilters = {
  borough: string[];
  cuisine: string[];
  grade: string[];
  risk: string[];
  criticalOnly: "all" | "critical" | "non_critical";
  search: string;
  limit: number;
};

type Props = {
  options: FilterOptions | null;
  applied: AppliedFilters;
  onApply: (filters: AppliedFilters) => void;
};

const emptyFilters: AppliedFilters = {
  borough: [],
  cuisine: [],
  grade: [],
  risk: [],
  criticalOnly: "all",
  search: "",
  limit: 5000
};

export function FilterPanel({ options, applied, onApply }: Props) {
  const [staged, setStaged] = useState<AppliedFilters>(applied);

  const hasPendingChanges = useMemo(() => {
    return JSON.stringify(staged) !== JSON.stringify(applied);
  }, [staged, applied]);

  return (
    <aside className="panel">
      <div className="panel-header">
        <h2>Filters</h2>
        <p>Select filters, then apply updates to refresh map data.</p>
      </div>

      {hasPendingChanges ? (
        <div className="notice pending">Filters ready - click Apply</div>
      ) : (
        <div className="notice ok">Applied filters are in sync</div>
      )}

      <label className="field">
        Borough
        <select
          multiple
          value={staged.borough}
          onChange={(event) =>
            setStaged((prev) => ({
              ...prev,
              borough: Array.from(event.target.selectedOptions).map((o) => o.value)
            }))
          }
        >
          {(options?.boroughs ?? []).map((borough) => (
            <option key={borough} value={borough}>
              {borough}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        Cuisine
        <select
          multiple
          value={staged.cuisine}
          onChange={(event) =>
            setStaged((prev) => ({
              ...prev,
              cuisine: Array.from(event.target.selectedOptions).map((o) => o.value)
            }))
          }
        >
          {(options?.cuisines ?? []).map((cuisine) => (
            <option key={cuisine} value={cuisine}>
              {cuisine}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        Grade
        <select
          multiple
          value={staged.grade}
          onChange={(event) =>
            setStaged((prev) => ({
              ...prev,
              grade: Array.from(event.target.selectedOptions).map((o) => o.value)
            }))
          }
        >
          {(options?.grades ?? []).map((grade) => (
            <option key={grade} value={grade}>
              {grade}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        Risk
        <select
          multiple
          value={staged.risk}
          onChange={(event) =>
            setStaged((prev) => ({
              ...prev,
              risk: Array.from(event.target.selectedOptions).map((o) => o.value)
            }))
          }
        >
          {(options?.risk_levels ?? []).map((risk) => (
            <option key={risk} value={risk}>
              {risk}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        Critical Violations
        <select
          value={staged.criticalOnly}
          onChange={(event) =>
            setStaged((prev) => ({
              ...prev,
              criticalOnly: event.target.value as AppliedFilters["criticalOnly"]
            }))
          }
        >
          <option value="all">All restaurants</option>
          <option value="critical">Critical violations only</option>
          <option value="non_critical">No critical violations</option>
        </select>
      </label>

      <label className="field">
        Restaurant Search
        <input
          type="text"
          value={staged.search}
          onChange={(event) =>
            setStaged((prev) => ({
              ...prev,
              search: event.target.value
            }))
          }
          placeholder="Type a restaurant name"
        />
      </label>

      <div className="actions">
        <button className="btn btn-primary" onClick={() => onApply(staged)}>
          Apply
        </button>
        <button className="btn btn-secondary" onClick={() => setStaged(emptyFilters)}>
          Clear
        </button>
      </div>
    </aside>
  );
}

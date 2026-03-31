import { useMemo } from "react";

import type { SummaryResponse } from "../types";

type Props = {
  summary: SummaryResponse | null;
};

function maxValue(values: number[]): number {
  if (!values.length) return 1;
  return Math.max(...values, 1);
}

export function IntelligencePanel({ summary }: Props) {
  const boroughMax = useMemo(
    () => maxValue((summary?.borough_scores ?? []).map((item) => item.avg_score)),
    [summary]
  );
  const cuisineMax = useMemo(
    () => maxValue((summary?.top_cuisines_critical ?? []).map((item) => item.critical_violations)),
    [summary]
  );
  const gradeMax = useMemo(
    () => maxValue((summary?.grade_distribution ?? []).map((item) => item.count)),
    [summary]
  );

  if (!summary) {
    return <section className="intel-panel">Loading intelligence feed...</section>;
  }

  return (
    <section className="intel-panel">
      <h2>Intelligence Feed</h2>
      <p>Live summary of hygiene signals from the current filtered map scope.</p>

      <div className="intel-block">
        <h3>Borough Average Scores</h3>
        {(summary.borough_scores || []).slice(0, 5).map((item) => (
          <div className="intel-row" key={item.borough}>
            <span>{item.borough}</span>
            <div className="bar">
              <div
                className="bar-fill amber"
                style={{ width: `${Math.max((item.avg_score / boroughMax) * 100, 8)}%` }}
              />
            </div>
            <strong>{item.avg_score.toFixed(1)}</strong>
          </div>
        ))}
      </div>

      <div className="intel-block">
        <h3>Grade Distribution</h3>
        {(summary.grade_distribution || []).slice(0, 5).map((item) => (
          <div className="intel-row" key={item.grade}>
            <span>{item.grade}</span>
            <div className="bar">
              <div
                className="bar-fill blue"
                style={{ width: `${Math.max((item.count / gradeMax) * 100, 8)}%` }}
              />
            </div>
            <strong>{item.count}</strong>
          </div>
        ))}
      </div>

      <div className="intel-block">
        <h3>Top Critical-Violation Cuisines</h3>
        {(summary.top_cuisines_critical || []).slice(0, 6).map((item) => (
          <div className="intel-row" key={item.cuisine_type}>
            <span>{item.cuisine_type}</span>
            <div className="bar">
              <div
                className="bar-fill red"
                style={{
                  width: `${Math.max((item.critical_violations / cuisineMax) * 100, 8)}%`
                }}
              />
            </div>
            <strong>{item.critical_violations}</strong>
          </div>
        ))}
      </div>

      <div className="intel-block">
        <h3>12-Month Score Trend</h3>
        <div className="trend-list">
          {(summary.monthly_trend || []).slice(-6).map((item) => (
            <div className="trend-item" key={item.month}>
              <span>{item.month}</span>
              <strong>{item.avg_score.toFixed(1)}</strong>
              <small>{item.inspections} inspections</small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

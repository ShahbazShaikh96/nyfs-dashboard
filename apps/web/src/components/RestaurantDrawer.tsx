import type { RestaurantHistoryResponse } from "../types";
import { RestaurantPhoto } from "./RestaurantPhoto";

type Props = {
  history: RestaurantHistoryResponse | null;
  open: boolean;
  loading: boolean;
  onClose: () => void;
};

export function RestaurantDrawer({ history, open, loading, onClose }: Props) {
  if (!open) return null;

  return (
    <aside className="drawer-overlay" role="dialog" aria-modal="true">
      <div className="drawer">
        <div className="drawer-head">
          <div>
            <h2>{history?.restaurant_name ?? "Restaurant Detail"}</h2>
            <p>
              {history ? `${history.borough} • ${history.cuisine_type}` : "Loading restaurant details"}
            </p>
          </div>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>

        {loading ? <div className="drawer-status">Loading history...</div> : null}

        {!loading && history ? (
          <div className="drawer-body">
            <section className="drawer-profile">
              <RestaurantPhoto
                photoUrl={history.photo_url}
                restaurantName={history.restaurant_name}
                cuisineType={history.cuisine_type}
              />
              <div className="drawer-profile-text">
                <div>
                  <strong>Street:</strong> {history.street_name}
                </div>
                <div>
                  <strong>Address:</strong> {history.full_address}
                </div>
              </div>
            </section>
            {history.points.slice(0, 12).map((point, index) => (
              <article key={`${point.inspection_date}-${index}`} className="history-card">
                <div className="history-top">
                  <strong>{point.inspection_date ?? "Unknown date"}</strong>
                  <span className={`pill ${point.risk_level.toLowerCase()}`}>{point.risk_level}</span>
                </div>
                <p>
                  Score: <strong>{point.inspection_score.toFixed(0)}</strong> | Grade:{" "}
                  <strong>{point.inspection_grade}</strong>
                </p>
                <p>
                  Critical violations: <strong>{point.critical_violations}</strong>
                </p>
                {point.violations ? <small>{point.violations}</small> : null}
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </aside>
  );
}

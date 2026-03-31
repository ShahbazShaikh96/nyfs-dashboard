import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Marker, Popup, Map } from "react-map-gl/maplibre";
import { useMemo, useState } from "react";

import type { Restaurant } from "../types";

const riskColors: Record<string, string> = {
  Low: "#2E8B57",
  Medium: "#E3A008",
  High: "#D64545"
};

type Props = {
  restaurants: Restaurant[];
  selectedRestaurantId: number | null;
  onSelectRestaurant: (restaurantId: number) => void;
};

export function MapView({ restaurants, selectedRestaurantId, onSelectRestaurant }: Props) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const hoveredRestaurant = useMemo(
    () => restaurants.find((r) => r.restaurant_id === hoveredId) ?? null,
    [hoveredId, restaurants]
  );

  return (
    <div className="map-shell">
      <Map
        mapLib={maplibregl}
        initialViewState={{ longitude: -74.006, latitude: 40.7128, zoom: 10 }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      >
        {restaurants.map((restaurant) => (
          <Marker
            key={restaurant.restaurant_id}
            longitude={restaurant.longitude}
            latitude={restaurant.latitude}
            anchor="center"
          >
            <button
              type="button"
              className={`marker ${
                selectedRestaurantId === restaurant.restaurant_id ? "selected" : ""
              }`}
              style={{ backgroundColor: riskColors[restaurant.risk_level] ?? "#64748B" }}
              onMouseEnter={() => setHoveredId(restaurant.restaurant_id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => onSelectRestaurant(restaurant.restaurant_id)}
              aria-label={restaurant.restaurant_name}
            />
          </Marker>
        ))}

        {hoveredRestaurant ? (
          <Popup
            longitude={hoveredRestaurant.longitude}
            latitude={hoveredRestaurant.latitude}
            closeButton={false}
            closeOnClick={false}
            anchor="top"
            offset={16}
          >
            <div className="tooltip-card">
              <div className="tooltip-title">{hoveredRestaurant.restaurant_name}</div>
              <div className="tooltip-row">Rating: Grade {hoveredRestaurant.inspection_grade}</div>
              <div className="tooltip-row">Cuisine: {hoveredRestaurant.cuisine_type}</div>
              <div className="tooltip-row">Location: {hoveredRestaurant.borough}</div>
            </div>
          </Popup>
        ) : null}
      </Map>
    </div>
  );
}

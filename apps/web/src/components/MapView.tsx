import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Marker, Popup, Map } from "react-map-gl/maplibre";
import { useMemo, useState } from "react";
import type { StyleSpecification } from "maplibre-gl";

import type { Restaurant } from "../types";
import { RestaurantPhoto } from "./RestaurantPhoto";

const riskColors: Record<string, string> = {
  Low: "#2E8B57",
  Medium: "#E3A008",
  High: "#D64545"
};

type Props = {
  restaurants: Restaurant[];
  selectedRestaurantId: number | null;
  onSelectRestaurant: (restaurantId: number) => void;
  mobileMode: boolean;
};

const standardStyle = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

const realisticStyle: StyleSpecification = {
  version: 8,
  sources: {
    esri: {
      type: "raster",
      tiles: [
        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
      ],
      tileSize: 256,
      attribution: "Esri, Maxar, Earthstar Geographics"
    }
  },
  layers: [
    {
      id: "esri-world-imagery",
      type: "raster",
      source: "esri"
    }
  ]
};

export function MapView({ restaurants, selectedRestaurantId, onSelectRestaurant, mobileMode }: Props) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [mapTheme, setMapTheme] = useState<"standard" | "realistic">("realistic");
  const hoveredRestaurant = useMemo(
    () => restaurants.find((r) => r.restaurant_id === hoveredId) ?? null,
    [hoveredId, restaurants]
  );
  const selectedRestaurant = useMemo(
    () => restaurants.find((r) => r.restaurant_id === selectedRestaurantId) ?? null,
    [selectedRestaurantId, restaurants]
  );
  const activePopupRestaurant = mobileMode ? selectedRestaurant : hoveredRestaurant;

  return (
    <div className="map-shell">
      <div className="map-theme-switch">
        <button
          className={`theme-btn ${mapTheme === "realistic" ? "active" : ""}`}
          onClick={() => setMapTheme("realistic")}
          type="button"
        >
          Realistic
        </button>
        <button
          className={`theme-btn ${mapTheme === "standard" ? "active" : ""}`}
          onClick={() => setMapTheme("standard")}
          type="button"
        >
          Standard
        </button>
      </div>
      <Map
        mapLib={maplibregl}
        initialViewState={{ longitude: -74.006, latitude: 40.7128, zoom: 10 }}
        style={{ width: "100%", height: "100%" }}
        mapStyle={mapTheme === "realistic" ? realisticStyle : standardStyle}
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
              onMouseEnter={
                mobileMode ? undefined : () => setHoveredId(restaurant.restaurant_id)
              }
              onMouseLeave={mobileMode ? undefined : () => setHoveredId(null)}
              onClick={() => onSelectRestaurant(restaurant.restaurant_id)}
              aria-label={restaurant.restaurant_name}
            />
          </Marker>
        ))}

        {activePopupRestaurant ? (
          <Popup
            longitude={activePopupRestaurant.longitude}
            latitude={activePopupRestaurant.latitude}
            closeButton={false}
            closeOnClick={false}
            anchor="top"
            offset={16}
          >
            <div className="tooltip-card">
              <RestaurantPhoto
                photoUrl={activePopupRestaurant.photo_url}
                restaurantName={activePopupRestaurant.restaurant_name}
                cuisineType={activePopupRestaurant.cuisine_type}
              />
              <div className="tooltip-title">{activePopupRestaurant.restaurant_name}</div>
              <div className="tooltip-row">
                Safety Signal:{" "}
                <span
                  className={`safety-pill ${activePopupRestaurant.risk_level.toLowerCase()}`}
                >
                  {activePopupRestaurant.risk_level}
                </span>
              </div>
              <div className="tooltip-row">
                Rating: Grade {activePopupRestaurant.inspection_grade || "Pending"}
              </div>
              <div className="tooltip-row">Cuisine: {activePopupRestaurant.cuisine_type}</div>
              <div className="tooltip-row">Location: {activePopupRestaurant.borough}</div>
              <div className="tooltip-row">Street: {activePopupRestaurant.street_name}</div>
              <div className="tooltip-row">{activePopupRestaurant.full_address}</div>
            </div>
          </Popup>
        ) : null}
      </Map>
    </div>
  );
}

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

export function MapView({ restaurants, selectedRestaurantId, onSelectRestaurant }: Props) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [mapTheme, setMapTheme] = useState<"standard" | "realistic">("realistic");
  const hoveredRestaurant = useMemo(
    () => restaurants.find((r) => r.restaurant_id === hoveredId) ?? null,
    [hoveredId, restaurants]
  );

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
              <RestaurantPhoto
                photoUrl={hoveredRestaurant.photo_url}
                restaurantName={hoveredRestaurant.restaurant_name}
                cuisineType={hoveredRestaurant.cuisine_type}
              />
              <div className="tooltip-title">{hoveredRestaurant.restaurant_name}</div>
              <div className="tooltip-row">
                Rating: Grade {hoveredRestaurant.inspection_grade || "Pending"}
              </div>
              <div className="tooltip-row">Cuisine: {hoveredRestaurant.cuisine_type}</div>
              <div className="tooltip-row">Location: {hoveredRestaurant.borough}</div>
              <div className="tooltip-row">Street: {hoveredRestaurant.street_name}</div>
              <div className="tooltip-row">{hoveredRestaurant.full_address}</div>
            </div>
          </Popup>
        ) : null}
      </Map>
    </div>
  );
}

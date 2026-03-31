from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    boroughs: list[str]
    cuisines: list[str]
    grades: list[str]
    risk_levels: list[str]


class RestaurantFeature(BaseModel):
    restaurant_id: int
    restaurant_name: str
    borough: str
    cuisine_type: str
    inspection_grade: str
    inspection_score: float
    risk_level: str
    risk_score: float
    has_critical_violations: bool
    critical_violations: int
    latest_inspection_date: str | None
    full_address: str
    latitude: float
    longitude: float


class RestaurantsResponse(BaseModel):
    total: int
    applied_filters: dict[str, Any]
    restaurants: list[RestaurantFeature]


class RestaurantHistoryPoint(BaseModel):
    inspection_date: str | None
    inspection_score: float
    inspection_grade: str
    critical_violations: int
    risk_level: str
    risk_score: float
    inspection_type: str | None
    action: str | None
    violations: str | None


class RestaurantHistoryResponse(BaseModel):
    restaurant_id: int
    restaurant_name: str
    borough: str
    cuisine_type: str
    points: list[RestaurantHistoryPoint]

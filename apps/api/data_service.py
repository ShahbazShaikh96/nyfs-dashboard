from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import pandas as pd

from settings import HISTORY_DATA_PATH, LATEST_DATA_PATH, METADATA_PATH


DATE_COLUMNS = ["inspection_date", "record_date"]


def _load_csv(path: str, parse_dates: list[str]) -> pd.DataFrame:
    dataframe = pd.read_csv(path, low_memory=False)
    for column in parse_dates:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(dataframe[column], errors="coerce")
    return dataframe


@lru_cache(maxsize=1)
def load_latest_restaurants() -> pd.DataFrame:
    df = _load_csv(str(LATEST_DATA_PATH), DATE_COLUMNS)
    numeric_fields = ["inspection_score", "risk_score", "latitude", "longitude"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    if "restaurant_id" in df.columns:
        df["restaurant_id"] = pd.to_numeric(df["restaurant_id"], errors="coerce").astype("Int64")
    return df


@lru_cache(maxsize=1)
def load_restaurant_history() -> pd.DataFrame:
    df = _load_csv(str(HISTORY_DATA_PATH), DATE_COLUMNS)
    numeric_fields = ["inspection_score", "risk_score", "critical_violations"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    if "restaurant_id" in df.columns:
        df["restaurant_id"] = pd.to_numeric(df["restaurant_id"], errors="coerce").astype("Int64")
    return df


@lru_cache(maxsize=1)
def load_metadata() -> dict[str, Any]:
    if not METADATA_PATH.exists():
        return {}
    return json.loads(METADATA_PATH.read_text())


def invalidate_cache() -> None:
    load_latest_restaurants.cache_clear()
    load_restaurant_history.cache_clear()
    load_metadata.cache_clear()


def available_filters(df: pd.DataFrame) -> dict[str, list[str]]:
    return {
        "boroughs": sorted(df["borough"].dropna().astype(str).unique().tolist()),
        "cuisines": sorted(df["cuisine_type"].dropna().astype(str).unique().tolist()),
        "grades": sorted(df["inspection_grade"].dropna().astype(str).unique().tolist()),
        "risk_levels": sorted(df["risk_level"].dropna().astype(str).unique().tolist()),
    }


def apply_restaurant_filters(
    dataframe: pd.DataFrame,
    boroughs: list[str] | None = None,
    cuisines: list[str] | None = None,
    grades: list[str] | None = None,
    risk_levels: list[str] | None = None,
    critical_only: bool | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    filtered = dataframe.copy()

    if boroughs:
        filtered = filtered[filtered["borough"].isin(boroughs)]
    if cuisines:
        filtered = filtered[filtered["cuisine_type"].isin(cuisines)]
    if grades:
        filtered = filtered[filtered["inspection_grade"].isin(grades)]
    if risk_levels:
        filtered = filtered[filtered["risk_level"].isin(risk_levels)]
    if critical_only is True:
        filtered = filtered[filtered["has_critical_violations"]]
    if critical_only is False:
        filtered = filtered[~filtered["has_critical_violations"]]

    if search:
        filtered = filtered[
            filtered["restaurant_name"].astype(str).str.contains(search, case=False, na=False)
        ]

    if start_date:
        start = pd.to_datetime(start_date, errors="coerce")
        if pd.notna(start):
            filtered = filtered[filtered["inspection_date"] >= start]
    if end_date:
        end = pd.to_datetime(end_date, errors="coerce")
        if pd.notna(end):
            filtered = filtered[filtered["inspection_date"] <= end]

    return filtered


def serialize_restaurants(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    if dataframe.empty:
        return []
    rows: list[dict[str, Any]] = []
    for _, row in dataframe.iterrows():
        if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
            continue
        rows.append(
            {
                "restaurant_id": int(row["restaurant_id"]),
                "restaurant_name": str(row["restaurant_name"]),
                "borough": str(row["borough"]),
                "cuisine_type": str(row["cuisine_type"]),
                "inspection_grade": str(row["inspection_grade"]),
                "inspection_score": float(row["inspection_score"]),
                "risk_level": str(row["risk_level"]),
                "risk_score": float(row["risk_score"]),
                "has_critical_violations": bool(row["has_critical_violations"]),
                "critical_violations": int(row["critical_violations"]),
                "latest_inspection_date": (
                    row["inspection_date"].strftime("%Y-%m-%d")
                    if pd.notna(row["inspection_date"])
                    else None
                ),
                "full_address": str(row["full_address"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }
        )
    return rows


def serialize_history(history_df: pd.DataFrame) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for _, row in history_df.iterrows():
        points.append(
            {
                "inspection_date": (
                    row["inspection_date"].strftime("%Y-%m-%d")
                    if pd.notna(row["inspection_date"])
                    else None
                ),
                "inspection_score": float(row["inspection_score"]),
                "inspection_grade": str(row["inspection_grade"]),
                "critical_violations": int(row["critical_violations"]),
                "risk_level": str(row["risk_level"]),
                "risk_score": float(row["risk_score"]),
                "inspection_type": str(row.get("inspection_type") or ""),
                "action": str(row.get("action") or ""),
                "violations": str(row.get("violations") or ""),
            }
        )
    return points

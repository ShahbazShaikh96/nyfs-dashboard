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


def _street_name(full_address: str) -> str:
    # Keep this simple and deterministic: drop leading street number if present.
    value = (full_address or "").strip()
    if not value:
        return "Unknown street"
    parts = value.split(maxsplit=1)
    if len(parts) == 2 and parts[0].replace("-", "").isdigit():
        return parts[1]
    return value


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
    cached_filtered_restaurants.cache_clear()


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


@lru_cache(maxsize=128)
def cached_filtered_restaurants(
    boroughs: tuple[str, ...],
    cuisines: tuple[str, ...],
    grades: tuple[str, ...],
    risk_levels: tuple[str, ...],
    critical_only: bool | None,
    search: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Cache filtered query results for repeated map requests with same parameters."""
    df = load_latest_restaurants()
    return apply_restaurant_filters(
        df,
        boroughs=list(boroughs) or None,
        cuisines=list(cuisines) or None,
        grades=list(grades) or None,
        risk_levels=list(risk_levels) or None,
        critical_only=critical_only,
        search=search or None,
        start_date=start_date or None,
        end_date=end_date or None,
    )


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
                "street_name": _street_name(str(row["full_address"])),
                "photo_url": None,
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


def build_summary(filtered_latest_df: pd.DataFrame, history_df: pd.DataFrame) -> dict[str, Any]:
    borough_scores = (
        filtered_latest_df.groupby("borough", as_index=False)["inspection_score"]
        .mean()
        .rename(columns={"inspection_score": "avg_score"})
        .sort_values("avg_score", ascending=False)
    )

    grade_distribution = (
        filtered_latest_df.groupby("inspection_grade", as_index=False)["restaurant_id"]
        .count()
        .rename(columns={"inspection_grade": "grade", "restaurant_id": "count"})
        .sort_values("count", ascending=False)
    )

    risk_distribution = (
        filtered_latest_df.groupby("risk_level", as_index=False)["restaurant_id"]
        .count()
        .rename(columns={"risk_level": "risk_level", "restaurant_id": "count"})
        .sort_values("count", ascending=False)
    )

    top_cuisines_critical = (
        filtered_latest_df.groupby("cuisine_type", as_index=False)["critical_violations"]
        .sum()
        .sort_values("critical_violations", ascending=False)
        .head(10)
    )

    filtered_ids = filtered_latest_df["restaurant_id"].dropna().astype("Int64").unique().tolist()
    scoped_history = history_df[history_df["restaurant_id"].isin(filtered_ids)].copy()
    monthly_trend = (
        scoped_history.dropna(subset=["inspection_date"])
        .assign(month=lambda frame: frame["inspection_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(
            avg_score=("inspection_score", "mean"),
            inspections=("restaurant_id", "count"),
        )
        .sort_values("month")
        .tail(12)
    )

    return {
        "borough_scores": borough_scores.to_dict(orient="records"),
        "grade_distribution": grade_distribution.to_dict(orient="records"),
        "risk_distribution": risk_distribution.to_dict(orient="records"),
        "top_cuisines_critical": top_cuisines_critical.to_dict(orient="records"),
        "monthly_trend": monthly_trend.to_dict(orient="records"),
    }

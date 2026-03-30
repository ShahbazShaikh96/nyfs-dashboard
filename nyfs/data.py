from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from nyfs import config


COLUMN_MAPPING = {
    "camis": "restaurant_id",
    "dba": "restaurant_name",
    "boro": "borough",
    "building": "building_number",
    "street": "street",
    "zipcode": "zip_code",
    "phone": "phone",
    "cuisine_description": "cuisine_type",
    "inspection_date": "inspection_date",
    "action": "action",
    "violation_code": "violation_code",
    "violation_description": "violation_description",
    "critical_flag": "critical_flag",
    "score": "inspection_score",
    "grade": "inspection_grade",
    "grade_date": "grade_date",
    "record_date": "record_date",
    "inspection_type": "inspection_type",
    "longitude": "longitude",
    "latitude": "latitude",
}

BOROUGH_STANDARDIZATION = {
    "BRONX": "Bronx",
    "BROOKLYN": "Brooklyn",
    "MANHATTAN": "Manhattan",
    "QUEENS": "Queens",
    "STATEN ISLAND": "Staten Island",
}

GRADE_ORDER = ["A", "B", "C", "Pending / Not Yet Graded", "Missing / Unknown"]
GRADE_COLORS = {
    "A": "#2E8B57",
    "B": "#E3A008",
    "C": "#D64545",
    "Pending / Not Yet Graded": "#7C8798",
    "Missing / Unknown": "#9CA3AF",
}
RISK_COLORS = {
    "Low": "#2E8B57",
    "Medium": "#E3A008",
    "High": "#D64545",
}


@dataclass
class DashboardData:
    inspections: pd.DataFrame
    latest: pd.DataFrame
    metadata: dict[str, Any]


def _candidate_paths(data_path: str | Path | None = None) -> list[Path]:
    if data_path:
        return [Path(data_path)]
    return [config.CLEAN_CACHE_CSV, config.LOCAL_SOURCE_CSV]


def _series_or_empty(dataframe: pd.DataFrame, column: str) -> pd.Series:
    if column in dataframe.columns:
        return dataframe[column]
    return pd.Series([pd.NA] * len(dataframe), index=dataframe.index)


def load_data(data_path: str | Path | None = None) -> pd.DataFrame:
    """Load either the cached clean dataset or a raw local CSV and normalize columns."""
    for candidate in _candidate_paths(data_path):
        if candidate.exists():
            df = pd.read_csv(candidate, low_memory=False)
            if "camis" in df.columns:
                df = df.rename(columns=COLUMN_MAPPING)
            return clean_data(df)
    raise FileNotFoundError("No NYFS data file was found.")


def clean_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize dates, categories, coordinates, and missing values."""
    df = dataframe.copy()

    for date_column in ["inspection_date", "grade_date", "record_date"]:
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

    text_columns = [
        "restaurant_name",
        "borough",
        "building_number",
        "street",
        "phone",
        "cuisine_type",
        "inspection_grade",
        "critical_flag",
        "inspection_type",
        "violation_code",
        "violation_description",
        "action",
    ]
    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].fillna("").astype(str).str.strip()

    df["borough"] = (
        _series_or_empty(df, "borough")
        .replace({"0": "", "": np.nan})
        .astype("string")
        .str.upper()
        .map(BOROUGH_STANDARDIZATION)
        .fillna("Unknown")
    )
    df["cuisine_type"] = (
        _series_or_empty(df, "cuisine_type").replace({"": np.nan}).fillna("Unknown")
    )
    df["inspection_grade"] = (
        _series_or_empty(df, "inspection_grade")
        .replace(
            {
                "": np.nan,
                "N": "Pending / Not Yet Graded",
                "P": "Pending / Not Yet Graded",
                "Z": "Pending / Not Yet Graded",
            }
        )
        .fillna("Missing / Unknown")
    )
    df["critical_flag"] = (
        _series_or_empty(df, "critical_flag")
        .replace({"": np.nan})
        .fillna("Not Applicable")
    )

    df["inspection_score"] = pd.to_numeric(
        _series_or_empty(df, "inspection_score"), errors="coerce"
    ).fillna(0)
    df["latitude"] = pd.to_numeric(_series_or_empty(df, "latitude"), errors="coerce")
    df["longitude"] = pd.to_numeric(_series_or_empty(df, "longitude"), errors="coerce")
    df["zip_code"] = pd.to_numeric(
        _series_or_empty(df, "zip_code"), errors="coerce"
    ).astype("Int64")
    df["restaurant_id"] = pd.to_numeric(
        _series_or_empty(df, "restaurant_id"), errors="coerce"
    ).astype("Int64")

    has_valid_coordinates = (
        df["latitude"].between(40.45, 40.95)
        & df["longitude"].between(-74.30, -73.65)
    )
    df.loc[~has_valid_coordinates, ["latitude", "longitude"]] = np.nan

    df = df[df["restaurant_id"].notna()].copy()
    df["restaurant_name"] = df["restaurant_name"].replace({"": "Unknown Restaurant"})
    df["full_address"] = (
        df["building_number"].fillna("").astype(str).str.strip()
        + " "
        + df["street"].fillna("").astype(str).str.strip()
    ).str.strip()
    df["full_address"] = df["full_address"].replace({"": "Address unavailable"})

    return df


def _first_non_empty(series: pd.Series, fallback: str = "") -> str:
    non_empty = series[series.fillna("").astype(str).str.strip() != ""]
    if non_empty.empty:
        return fallback
    return str(non_empty.iloc[0])


def _recency_penalty(days_since_inspection: float) -> int:
    if pd.isna(days_since_inspection):
        return 8
    if days_since_inspection > 365:
        return 8
    if days_since_inspection > 180:
        return 4
    return 0


def _grade_penalty(grade: str) -> int:
    return {
        "A": 0,
        "B": 6,
        "C": 12,
        "Pending / Not Yet Graded": 4,
        "Missing / Unknown": 5,
    }.get(grade, 5)


def _risk_level_from_score(score: float) -> str:
    if score >= 40:
        return "High"
    if score >= 20:
        return "Medium"
    return "Low"


def create_features(
    dataframe: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
) -> DashboardData:
    """Collapse row-level violations into inspection-level and latest-restaurant features."""
    df = dataframe.copy()
    reference = reference_date
    if reference is None:
        candidate = df["record_date"].max() if "record_date" in df.columns else pd.NaT
        reference = candidate if pd.notna(candidate) else pd.Timestamp(datetime.now(UTC))
    df["is_critical"] = df["critical_flag"].eq("Critical")

    inspections = (
        df.sort_values(["restaurant_id", "inspection_date", "record_date"])
        .groupby(["restaurant_id", "inspection_date"], dropna=False)
        .agg(
            restaurant_name=("restaurant_name", _first_non_empty),
            borough=("borough", _first_non_empty),
            cuisine_type=("cuisine_type", _first_non_empty),
            full_address=("full_address", _first_non_empty),
            zip_code=("zip_code", "max"),
            phone=("phone", _first_non_empty),
            inspection_type=("inspection_type", _first_non_empty),
            action=("action", _first_non_empty),
            inspection_grade=("inspection_grade", _first_non_empty),
            inspection_score=("inspection_score", "max"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
            record_date=("record_date", "max"),
            critical_violations=("is_critical", "sum"),
            total_violations=(
                "violation_code",
                lambda x: x.fillna("").astype(str).str.strip().ne("").sum(),
            ),
            violations=(
                "violation_description",
                lambda x: " | ".join(
                    pd.Series(
                        [item.strip() for item in x if isinstance(item, str) and item.strip()]
                    ).drop_duplicates()
                ),
            ),
        )
        .reset_index()
    )

    inspections["has_critical_violations"] = inspections["critical_violations"] > 0
    inspections["days_since_inspection"] = (
        reference.normalize() - inspections["inspection_date"]
    ).dt.days

    performance_flag = (
        inspections["inspection_score"].ge(28)
        | inspections["inspection_grade"].isin(["B", "C"])
    )
    inspections = inspections.sort_values(
        ["restaurant_id", "inspection_date", "record_date"],
        ascending=[True, False, False],
    )
    inspections["recent_poor_results"] = (
        performance_flag.loc[inspections.index]
        .astype(int)
        .groupby(inspections["restaurant_id"])
        .rolling(window=3, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )

    inspections["risk_score"] = (
        inspections["inspection_score"]
        + inspections["critical_violations"] * 8
        + inspections["inspection_grade"].map(_grade_penalty)
        + inspections["days_since_inspection"].apply(_recency_penalty)
        + (inspections["recent_poor_results"] - 1).clip(lower=0) * 4
    ).clip(lower=0, upper=100)
    inspections["risk_level"] = inspections["risk_score"].apply(_risk_level_from_score)
    inspections["risk_summary"] = np.select(
        [
            inspections["risk_level"].eq("Low"),
            inspections["risk_level"].eq("Medium"),
        ],
        [
            "Low risk: the latest inspection looks comparatively favorable, but users should still review recent details.",
            "Medium risk: there were notable issues, a weaker grade, or an older inspection worth checking before deciding.",
        ],
        default="High risk: the latest inspection suggests more serious or repeated concerns that deserve caution.",
    )

    latest = (
        inspections.sort_values(
            ["restaurant_id", "inspection_date", "record_date"],
            ascending=[True, False, False],
        )
        .groupby("restaurant_id", as_index=False)
        .first()
    )

    latest["critical_violation_label"] = np.where(
        latest["has_critical_violations"], "Critical issues found", "No critical issues found"
    )
    latest["map_color_grade"] = latest["inspection_grade"]
    latest["map_color_risk"] = latest["risk_level"]

    metadata = {
        "last_updated": reference.isoformat() if pd.notna(reference) else None,
        "halal_supported": False,
        "halal_note": (
            "Halal filtering is not currently supported because the NYC inspection dataset "
            "does not provide a trustworthy halal-specific field."
        ),
    }
    return DashboardData(inspections=inspections, latest=latest, metadata=metadata)


def load_dashboard_data() -> DashboardData:
    """Load the cached dashboard store when available, otherwise build from local CSV."""
    metadata: dict[str, Any] = {}
    if (
        config.INSPECTIONS_CACHE_CSV.exists()
        and config.LATEST_CACHE_CSV.exists()
    ):
        inspections = pd.read_csv(
            config.INSPECTIONS_CACHE_CSV,
            parse_dates=["inspection_date", "record_date"],
            low_memory=False,
        )
        latest = pd.read_csv(
            config.LATEST_CACHE_CSV,
            parse_dates=["inspection_date", "record_date"],
            low_memory=False,
        )
        for frame in (inspections, latest):
            for column in ["inspection_date", "record_date"]:
                if column in frame.columns:
                    frame[column] = pd.to_datetime(frame[column], errors="coerce")
        if config.REFRESH_METADATA_JSON.exists():
            metadata = json.loads(config.REFRESH_METADATA_JSON.read_text())
        return DashboardData(inspections=inspections, latest=latest, metadata=metadata)

    cleaned = load_data()
    dashboard_data = create_features(cleaned)
    return dashboard_data

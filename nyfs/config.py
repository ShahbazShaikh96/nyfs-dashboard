from __future__ import annotations

import os
from pathlib import Path


APP_TITLE = "NY Food Safety Dashboard"
DATASET_ID = "43nn-pn8j"
SOCRATA_QUERY_URL = f"https://data.cityofnewyork.us/api/v3/views/{DATASET_ID}/query.json"
SOCRATA_RESOURCE_URL = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

LOCAL_SOURCE_CSV = ROOT_DIR / "nyc_inspection_data.csv"
RAW_CACHE_CSV = DATA_DIR / "nyc_inspections_raw.csv"
CLEAN_CACHE_CSV = DATA_DIR / "nyc_inspections_clean.csv"
INSPECTIONS_CACHE_CSV = DATA_DIR / "restaurant_inspections.csv"
LATEST_CACHE_CSV = DATA_DIR / "latest_restaurants.csv"
REFRESH_METADATA_JSON = DATA_DIR / "refresh_metadata.json"

DEFAULT_API_MODE = os.getenv("NYFS_API_MODE", "auto")
DEFAULT_PAGE_SIZE = int(os.getenv("NYFS_PAGE_SIZE", "20000"))
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("NYFS_TIMEOUT_SECONDS", "60"))
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN") or os.getenv("NYFS_SOCRATA_APP_TOKEN")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

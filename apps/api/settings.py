from __future__ import annotations

import os
import tempfile
from pathlib import Path


API_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = API_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

LATEST_DATA_PATH = DATA_DIR / "latest_restaurants.csv"
HISTORY_DATA_PATH = DATA_DIR / "restaurant_inspections.csv"
METADATA_PATH = DATA_DIR / "refresh_metadata.json"

DEFAULT_RESULT_LIMIT = 5000
MAX_RESULT_LIMIT = 12000

FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "").strip()
PHOTO_ENRICHMENT_ENABLED = bool(FOURSQUARE_API_KEY)
PHOTO_CACHE_PATH = Path(
    os.getenv(
        "NYFS_PHOTO_CACHE_PATH",
        str(Path(tempfile.gettempdir()) / "nyfs_photo_cache.json"),
    )
)

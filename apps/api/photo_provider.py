from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from settings import FOURSQUARE_API_KEY, PHOTO_CACHE_PATH


class FoursquarePhotoProvider:
    """Lightweight enrichment client for optional third-party photos."""

    def __init__(self, api_key: str, cache_path: Path):
        self.api_key = api_key
        self.cache_path = cache_path
        self.session = requests.Session()
        self.session.headers.update({"Authorization": api_key, "accept": "application/json"})
        self.cache = self._load_cache()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        if not self.cache_path.exists():
            return {}
        try:
            raw = json.loads(self.cache_path.read_text())
            if isinstance(raw, dict):
                return raw
        except Exception:
            pass
        return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2))

    def get_photo_for_restaurant(
        self,
        *,
        restaurant_id: int,
        restaurant_name: str,
        latitude: float | None,
        longitude: float | None,
    ) -> tuple[str | None, str | None]:
        cache_key = str(restaurant_id)
        cached = self.cache.get(cache_key)
        if cached:
            return cached.get("photo_url"), cached.get("source")

        if not self.enabled or latitude is None or longitude is None:
            return None, None

        photo_url = self._fetch_photo_url(restaurant_name, latitude, longitude)
        source = "Foursquare" if photo_url else None
        self.cache[cache_key] = {
            "photo_url": photo_url,
            "source": source,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self._save_cache()
        return photo_url, source

    def _fetch_photo_url(self, restaurant_name: str, latitude: float, longitude: float) -> str | None:
        try:
            search_response = self.session.get(
                "https://api.foursquare.com/v3/places/search",
                params={
                    "query": restaurant_name,
                    "ll": f"{latitude},{longitude}",
                    "radius": 200,
                    "limit": 1,
                },
                timeout=8,
            )
            search_response.raise_for_status()
            results = search_response.json().get("results", [])
            if not results:
                return None

            fsq_id = results[0].get("fsq_id")
            if not fsq_id:
                return None

            photo_response = self.session.get(
                f"https://api.foursquare.com/v3/places/{fsq_id}/photos",
                params={"limit": 1, "sort": "POPULAR"},
                timeout=8,
            )
            photo_response.raise_for_status()
            photos = photo_response.json()
            if not photos:
                return None

            first = photos[0]
            prefix = first.get("prefix")
            suffix = first.get("suffix")
            if not prefix or not suffix:
                return None
            return f"{prefix}original{suffix}"
        except Exception:
            return None


photo_provider = FoursquarePhotoProvider(
    api_key=FOURSQUARE_API_KEY,
    cache_path=PHOTO_CACHE_PATH,
)

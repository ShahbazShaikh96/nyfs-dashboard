from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from nyfs import config
from nyfs.data import create_features, load_data


LOGGER = logging.getLogger(__name__)


def _headers(include_token: bool = True) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "nyfs-dashboard/1.0",
    }
    if include_token and config.SOCRATA_APP_TOKEN:
        headers["X-App-Token"] = config.SOCRATA_APP_TOKEN
    return headers


def _extract_v3_rows(payload: dict[str, Any]) -> pd.DataFrame:
    if isinstance(payload.get("results"), list):
        return pd.DataFrame(payload["results"])

    if isinstance(payload.get("data"), list):
        rows = payload["data"]
        if not rows:
            return pd.DataFrame()

        if isinstance(rows[0], dict):
            return pd.DataFrame(rows)

        columns = payload.get("columns", [])
        column_names = [
            column.get("fieldName") or column.get("name") or f"column_{index}"
            for index, column in enumerate(columns)
        ]
        return pd.DataFrame(rows, columns=column_names[: len(rows[0])])

    raise ValueError("Unrecognized response shape from Socrata v3 query endpoint.")


def _fetch_v3_page(
    session: requests.Session,
    page_number: int,
    page_size: int,
    timeout_seconds: int,
) -> pd.DataFrame:
    payload = {
        "query": "SELECT *",
        "page": {"pageNumber": page_number, "pageSize": page_size},
        "includeSynthetic": False,
    }
    response = session.post(
        config.SOCRATA_QUERY_URL,
        headers=_headers(include_token=True),
        json=payload,
        timeout=timeout_seconds,
    )
    if response.status_code == 403 and config.SOCRATA_APP_TOKEN:
        # Retry unauthenticated in case the provided token is invalid or expired.
        LOGGER.warning("v3 request returned 403; retrying once without app token.")
        response = session.post(
            config.SOCRATA_QUERY_URL,
            headers=_headers(include_token=False),
            json=payload,
            timeout=timeout_seconds,
        )
    response.raise_for_status()
    return _extract_v3_rows(response.json())


def _fetch_legacy_page(
    session: requests.Session,
    offset: int,
    page_size: int,
    timeout_seconds: int,
) -> pd.DataFrame:
    params = {
        "$limit": page_size,
        "$offset": offset,
    }
    response = session.get(
        config.SOCRATA_RESOURCE_URL,
        headers=_headers(include_token=True),
        params=params,
        timeout=timeout_seconds,
    )
    if response.status_code == 403 and config.SOCRATA_APP_TOKEN:
        LOGGER.warning("legacy request returned 403; retrying once without app token.")
        response = session.get(
            config.SOCRATA_RESOURCE_URL,
            headers=_headers(include_token=False),
            params=params,
            timeout=timeout_seconds,
        )
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list):
        raise ValueError("Legacy API returned an unexpected payload format.")
    return pd.DataFrame(rows)


def fetch_all_data(
    api_mode: str | None = None,
    page_size: int | None = None,
    timeout_seconds: int | None = None,
) -> pd.DataFrame:
    """Fetch the full restaurant inspection dataset with pagination."""
    mode = (api_mode or config.DEFAULT_API_MODE).lower()
    batch_size = page_size or config.DEFAULT_PAGE_SIZE
    timeout = timeout_seconds or config.DEFAULT_TIMEOUT_SECONDS

    session = requests.Session()
    frames: list[pd.DataFrame] = []

    LOGGER.info("Starting data refresh via Socrata API mode=%s", mode)

    def _fetch_v3_all() -> list[pd.DataFrame]:
        local_frames: list[pd.DataFrame] = []
        page_number = 1
        while True:
            page = _fetch_v3_page(session, page_number, batch_size, timeout)
            LOGGER.info("Fetched v3 page %s with %s rows", page_number, len(page))
            if page.empty:
                break
            local_frames.append(page)
            if len(page) < batch_size:
                break
            page_number += 1
        return local_frames

    def _fetch_legacy_all() -> list[pd.DataFrame]:
        local_frames: list[pd.DataFrame] = []
        offset = 0
        while True:
            page = _fetch_legacy_page(session, offset, batch_size, timeout)
            LOGGER.info("Fetched legacy offset %s with %s rows", offset, len(page))
            if page.empty:
                break
            local_frames.append(page)
            if len(page) < batch_size:
                break
            offset += batch_size
        return local_frames

    try:
        if mode == "v3":
            frames = _fetch_v3_all()
        elif mode == "legacy":
            frames = _fetch_legacy_all()
        elif mode == "auto":
            try:
                frames = _fetch_v3_all()
            except Exception as first_error:
                LOGGER.warning("v3 mode failed (%s). Falling back to legacy mode.", first_error)
                frames = _fetch_legacy_all()
        else:
            raise ValueError("api_mode must be 'auto', 'v3', or 'legacy'.")
    except requests.HTTPError as http_error:
        if http_error.response is not None and http_error.response.status_code == 403:
            raise RuntimeError(
                "Socrata API returned 403 Forbidden. "
                "Check SOCRATA_APP_TOKEN scope/validity or remove invalid token secret."
            ) from http_error
        raise

    if not frames:
        raise RuntimeError("No data was returned by the API.")

    combined = pd.concat(frames, ignore_index=True)
    LOGGER.info("Finished API refresh with %s rows", len(combined))
    return combined


def persist_dashboard_store(
    raw_df: pd.DataFrame,
    source_label: str,
    fallback_used: bool = False,
) -> dict[str, Any]:
    """Save raw, clean, and feature-engineered dashboard artifacts locally."""
    config.ensure_data_dir()

    raw_df.to_csv(config.RAW_CACHE_CSV, index=False)
    cleaned_df = load_data(config.RAW_CACHE_CSV)
    cleaned_df.to_csv(config.CLEAN_CACHE_CSV, index=False)

    dashboard_data = create_features(cleaned_df)
    dashboard_data.inspections.to_csv(config.INSPECTIONS_CACHE_CSV, index=False)
    dashboard_data.latest.to_csv(config.LATEST_CACHE_CSV, index=False)

    metadata = {
        "refreshed_at_utc": datetime.now(UTC).isoformat(),
        "source": source_label,
        "fallback_used": fallback_used,
        "raw_rows": int(len(raw_df)),
        "clean_rows": int(len(cleaned_df)),
        "inspection_rows": int(len(dashboard_data.inspections)),
        "latest_restaurants": int(len(dashboard_data.latest)),
        "halal_supported": False,
        "halal_note": (
            "The source inspection dataset does not include a reliable halal field, "
            "so NYFS does not currently offer halal filtering."
        ),
        "last_record_date": dashboard_data.metadata.get("last_updated"),
    }
    config.REFRESH_METADATA_JSON.write_text(json.dumps(metadata, indent=2))
    LOGGER.info("Saved dashboard artifacts to %s", config.DATA_DIR)
    return metadata


def refresh_dashboard_data(
    api_mode: str | None = None,
    allow_fallback: bool = True,
) -> dict[str, Any]:
    """Refresh local dashboard files from the API, falling back to the bundled CSV."""
    try:
        raw_df = fetch_all_data(api_mode=api_mode)
        return persist_dashboard_store(raw_df=raw_df, source_label="socrata_api")
    except Exception as exc:
        LOGGER.warning("API refresh failed: %s", exc)
        if not allow_fallback or not config.LOCAL_SOURCE_CSV.exists():
            raise

        fallback_df = pd.read_csv(config.LOCAL_SOURCE_CSV, low_memory=False)
        return persist_dashboard_store(
            raw_df=fallback_df,
            source_label="local_csv_fallback",
            fallback_used=True,
        )

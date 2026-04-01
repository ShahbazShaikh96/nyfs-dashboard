from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data_service import (
    available_filters,
    build_summary,
    cached_filtered_restaurants,
    invalidate_cache,
    load_latest_restaurants,
    load_metadata,
    load_restaurant_history,
    serialize_history,
    serialize_restaurants,
)
from schemas import FilterOptions, RestaurantHistoryResponse, RestaurantsResponse, SummaryResponse
from settings import DEFAULT_RESULT_LIMIT, MAX_RESULT_LIMIT


app = FastAPI(title="NYFS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/metadata")
def metadata() -> dict:
    return load_metadata()


@app.get("/api/v1/filters", response_model=FilterOptions)
def filters() -> FilterOptions:
    df = load_latest_restaurants()
    return FilterOptions(**available_filters(df))


@app.get("/api/v1/restaurants", response_model=RestaurantsResponse)
def restaurants(
    borough: list[str] = Query(default=[]),
    cuisine: list[str] = Query(default=[]),
    grade: list[str] = Query(default=[]),
    risk: list[str] = Query(default=[]),
    critical_only: bool | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    offset: int = 0,
    limit: int = DEFAULT_RESULT_LIMIT,
) -> RestaurantsResponse:
    filtered = cached_filtered_restaurants(
        tuple(sorted(borough)),
        tuple(sorted(cuisine)),
        tuple(sorted(grade)),
        tuple(sorted(risk)),
        critical_only,
        search or "",
        start_date or "",
        end_date or "",
    )
    filtered = filtered.sort_values(["risk_score", "inspection_score"], ascending=[False, False])
    safe_limit = max(1, min(limit, MAX_RESULT_LIMIT))
    safe_offset = max(0, offset)
    paged = filtered.iloc[safe_offset : safe_offset + safe_limit]
    return RestaurantsResponse(
        total=int(len(filtered)),
        offset=safe_offset,
        limit=safe_limit,
        applied_filters={
            "borough": borough,
            "cuisine": cuisine,
            "grade": grade,
            "risk": risk,
            "critical_only": critical_only,
            "search": search,
            "start_date": start_date,
            "end_date": end_date,
            "offset": safe_offset,
            "limit": safe_limit,
        },
        restaurants=serialize_restaurants(paged),
    )


@app.get("/api/v1/summary", response_model=SummaryResponse)
def summary(
    borough: list[str] = Query(default=[]),
    cuisine: list[str] = Query(default=[]),
    grade: list[str] = Query(default=[]),
    risk: list[str] = Query(default=[]),
    critical_only: bool | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> SummaryResponse:
    filtered = cached_filtered_restaurants(
        tuple(sorted(borough)),
        tuple(sorted(cuisine)),
        tuple(sorted(grade)),
        tuple(sorted(risk)),
        critical_only,
        search or "",
        start_date or "",
        end_date or "",
    )
    summary_data = build_summary(filtered, load_restaurant_history())
    return SummaryResponse(**summary_data)


@app.get("/api/v1/restaurants/{restaurant_id}/history", response_model=RestaurantHistoryResponse)
def restaurant_history(restaurant_id: int) -> RestaurantHistoryResponse:
    latest_df = load_latest_restaurants()
    match = latest_df[latest_df["restaurant_id"].eq(restaurant_id)]
    if match.empty:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    history_df = load_restaurant_history()
    points_df = history_df[history_df["restaurant_id"].eq(restaurant_id)].sort_values(
        "inspection_date", ascending=False
    )
    current = match.iloc[0]
    return RestaurantHistoryResponse(
        restaurant_id=restaurant_id,
        restaurant_name=str(current["restaurant_name"]),
        borough=str(current["borough"]),
        cuisine_type=str(current["cuisine_type"]),
        full_address=str(current["full_address"]),
        street_name=str(current.get("street_name", current["full_address"])),
        photo_url=None,
        points=serialize_history(points_df),
    )


@app.post("/api/v1/cache/invalidate")
def cache_invalidate() -> dict[str, str]:
    invalidate_cache()
    return {"status": "cache invalidated"}

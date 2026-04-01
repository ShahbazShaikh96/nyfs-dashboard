# NYFS API

FastAPI service that exposes geospatial and analytics endpoints for the next-generation NYFS frontend.

## Run

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

## Endpoints

- `GET /health`
- `GET /api/v1/metadata`
- `GET /api/v1/filters`
- `GET /api/v1/restaurants`
- `GET /api/v1/summary`
- `GET /api/v1/restaurants/{restaurant_id}/history`

`/api/v1/restaurants` supports server-side pagination via `offset` and `limit` query params.

## Optional Photo Enrichment

Restaurant detail supports optional third-party photo enrichment for selected restaurants only.

- Provider: Foursquare Places API
- Env var: `FOURSQUARE_API_KEY`
- Cache file: `NYFS_PHOTO_CACHE_PATH` (defaults to temp directory)

If no API key is set, the API continues to work and returns `photo_url: null`.

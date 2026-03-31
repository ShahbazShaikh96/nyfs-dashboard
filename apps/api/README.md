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
- `GET /api/v1/restaurants/{restaurant_id}/history`

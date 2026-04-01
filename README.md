# NYFS Dashboard

NYFS is a public NYC food safety intelligence product with:

- a scheduled data refresh pipeline (`update_data.py` + GitHub Actions),
- a FastAPI backend (`apps/api`),
- a React + MapLibre frontend (`apps/web`).

Streamlit UI files were intentionally removed to keep the repo focused and lean.

## Project Structure

```text
.
├── .github/workflows/update_data.yml
├── apps/
│   ├── api/
│   └── web/
├── data/
│   ├── latest_restaurants.csv
│   ├── refresh_metadata.json
│   └── restaurant_inspections.csv
├── nyfs/
│   ├── config.py
│   ├── data.py
│   └── ingestion.py
├── requirements.txt
├── update_data.py
└── render.yaml
```

## Data Refresh Pipeline

The dashboard does not hit NYC Open Data directly on each user request.

Flow:

1. GitHub Actions runs daily (`.github/workflows/update_data.yml`)
2. `python update_data.py --api-mode auto` fetches and processes latest data
3. Updated files in `data/` are committed back to `main`
4. Hosting platform redeploys from the latest commit

This keeps the site fast and available even when your local machine is off.

## Local Development

### 1) Refresh data locally

```bash
pip install -r requirements.txt
python update_data.py --api-mode auto
```

Optional higher API quota:

- `SOCRATA_APP_TOKEN`

### 2) Run API locally

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### 3) Run web app locally

```bash
cd apps/web
npm install
npm run dev
```

If needed, set `VITE_API_BASE_URL` to your API URL.

## Deploy on Render

This repo includes `render.yaml` Blueprint for:

- `nyfs-api` (Python web service)
- `nyfs-web` (static frontend)

After API deploy:

1. Copy API URL
2. Set `VITE_API_BASE_URL` on `nyfs-web`
3. Redeploy `nyfs-web`

Optional photo enrichment:

- Set `FOURSQUARE_API_KEY` on `nyfs-api`
- Selected restaurant details can show cached third-party photos with a source label

## Verify Automation

1. Run GitHub Action manually once from Actions tab
2. Confirm new commit updates `data/*.csv` and `data/refresh_metadata.json`
3. Confirm deployed app reflects the new timestamp/data after redeploy

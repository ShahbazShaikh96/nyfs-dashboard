# NY Food Safety Dashboard

NYFS is a public-facing Streamlit dashboard for exploring NYC restaurant inspection patterns. It is designed for everyday users who want a faster way to interpret grades, risk patterns, and borough or cuisine trends without digging through raw city data.

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── update_data.yml
├── .gitignore
├── .streamlit/
│   └── config.toml
├── app.py
├── data/
│   ├── latest_restaurants.csv
│   ├── refresh_metadata.json
│   └── restaurant_inspections.csv
├── nyfs/
│   ├── __init__.py
│   ├── config.py
│   ├── dashboard.py
│   ├── data.py
│   └── ingestion.py
├── requirements.txt
└── update_data.py
```

## Run Locally

1. Install dependencies: `pip install -r requirements.txt`
2. Refresh local data cache: `python update_data.py`
3. Start the app: `streamlit run app.py`

`data/latest_restaurants.csv`, `data/restaurant_inspections.csv`, and `data/refresh_metadata.json` are the deployable data artifacts the public app reads from. The larger raw and clean cache files are intentionally local-only and are not meant to be committed to GitHub.

## Socrata Token

If you have a Socrata application token, set one of these environment variables before running the refresh script:

- `SOCRATA_APP_TOKEN`
- `NYFS_SOCRATA_APP_TOKEN`

## Deployment

This project is ready for Streamlit Community Cloud:

1. Push the repository to GitHub.
2. In Streamlit Community Cloud, select the repo and use `app.py` as the entry point.
3. Add `SOCRATA_APP_TOKEN` as an optional secret in Streamlit if you want the app environment to have the same token available.
4. The app reads the committed files in `data/`, so it stays publicly accessible even when your laptop is turned off.

## Automated Daily Refresh

The repository includes a GitHub Actions workflow at `.github/workflows/update_data.yml`.

- It runs once every day on a schedule.
- It can also be run manually from the GitHub Actions tab.
- It installs dependencies, runs `python update_data.py --api-mode auto --no-fallback` (tries v3 first, then legacy), and commits only the deployable processed files back to the repository if anything changed.
- When that commit lands on GitHub, Streamlit Community Cloud can automatically redeploy the app with fresher data.

## Push To GitHub

1. Create a new GitHub repository.
2. Push this project folder to that repository.
3. In the repository settings, add an Actions secret named `SOCRATA_APP_TOKEN` if you want higher API rate limits for the daily refresh job.

## Connect To Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with GitHub.
2. Create a new app from your repository.
3. Set the main file path to `app.py`.
4. After the app is live, GitHub pushes from the refresh workflow will keep the hosted dashboard updated.

## Verify Daily Refresh

1. Open the GitHub repository Actions tab and run `Update NYFS Data` manually once.
2. Confirm that updated files appear in the `data/` folder and that a refresh commit is created when data changes.
3. Open the Streamlit app and confirm the visible last-updated timestamp changes after the workflow commit is deployed.

## Halal Filter

NYFS intentionally does not fabricate halal filtering. The NYC inspection dataset does not include a reliable halal-specific field, so the app explains that limitation instead of guessing.

## Next-Gen Platform (FastAPI + React Map)

This repository now also includes a production-style foundation for the next NYFS product:

- `apps/api`: FastAPI service over NYFS processed datasets
- `apps/web`: React + Vite + MapLibre map client

### Run API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Run Web Client

```bash
cd apps/web
npm install
cp .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` if your API runs on a different host/port.

## Deploy Next-Gen Publicly (Render)

This repo includes a Render blueprint: `render.yaml`.

### One-time setup

1. Open Render dashboard: https://dashboard.render.com/
2. Click **New** -> **Blueprint**
3. Connect GitHub repo: `ShahbazShaikh96/nyfs-dashboard`
4. Render will detect `render.yaml` and create:
   - `nyfs-api` (FastAPI web service)
   - `nyfs-web` (static Vite site)

### Required environment variable

After `nyfs-api` is deployed, copy its public URL and set this in `nyfs-web`:

- `VITE_API_BASE_URL=https://<your-nyfs-api-url>`

Then redeploy `nyfs-web`.

### Verify deployment

1. API health check:
   - `https://<your-nyfs-api-url>/health` should return `{"status":"ok"}`
2. Web app:
   - open `https://<your-nyfs-web-url>`
3. Functional checks:
   - map points load
   - filters apply
   - intelligence panel renders
   - clicking a marker opens detail drawer/history

### Notes

- Free plans may spin down when idle and wake on first request.
- Keep CORS open in API for now (already configured).
- If you later split hosting (for example Vercel + Render), only `VITE_API_BASE_URL` changes.

# DueTime

Know what your car needs before it breaks. Recalls, known failures at your mileage, overdue and skipped maintenance, and a fair private-sale price for any used car, in English and Spanish.

Built at Hacklanta 2026 · Social Good track (presented by Cox Automotive).

> The right to repair starts with the right to know what your car needs.

## Demo
- Live: [link]
- Video: [link]

## Features
- VIN decode, VIN photo scan, or manual year/make/model/mileage
- Open safety recalls in plain language
- Known problems by component, with whether your mileage is in the failure range
- Maintenance due now, plus skipped and declined services ranked by cost of ignoring them
- Fix-it-yourself vs. shop card: difficulty, tools, time, parts vs. shop cost
- "What's wrong with my car?": describe a symptom, get likely causes for your exact car with web sources to read more (Gemini + Google Search grounding)
- Buying mode: pre-purchase checklist, seller questions, private-sale price check
- English / Español
- Installable PWA; demo reports work offline once opened

## How it works
```
phone (PWA) ──► FastAPI ──► NHTSA vPIC / Recalls / Complaints (public APIs)
                   │──────► Tiger Data: complaint mileage curves + price comps (public data only)
                   ├──────► Groq (backup when Gemini is down)
                   └──────► Gemini: plain-language report, Spanish, VIN photo reading,
                            symptom lookup grounded in Google Search (returns sources)
```
Numbers come from data; words come from Gemini. The prompt forbids inventing recalls, complaint counts, mileages, or prices.

## Privacy (Zero Data)
- No accounts, cookies, analytics, or tracking.
- The API never logs VINs or lookups (run uvicorn with `--no-access-log`).
- VIN photos and symptom descriptions are processed in memory and never saved. Symptoms are sent by POST so they stay out of URLs.
- The service log lives only on the user's screen; they export it to their own device.
- The database holds public car data only. Craigslist seller fields (URL, VIN, location, description) are dropped on import.

---

## Team setup (do tonight)

### 1. Backend (Python 3.11+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY and DATABASE_URL
python -m scripts.cache_demo_cars     # saves NHTSA data for the 3 demo cars; check the counts
uvicorn app.main:app --reload --no-access-log
```
API docs: http://localhost:8000/docs

If a demo car shows 0 recalls and 0 complaints, NHTSA names the model differently. Fix `scripts/demo_cars.json` and rerun.

### 2. Tiger Data
1. Create a free service at Tiger Cloud and copy the connection string into `DATABASE_URL`.
2. `psql "$DATABASE_URL" -f db/schema.sql`
3. Complaints with mileage: download `FLAT_CMPL.zip` (or a `COMPLAINTS_RECEIVED_YYYY-YYYY.zip` chunk) from https://www.nhtsa.gov/nhtsa-datasets-and-apis, unzip, then
   `python -m scripts.load_complaints path/to/FLAT_CMPL.txt` (demo cars only; add `--all` for everything)
4. Listings: download `vehicles.csv` from https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data, then
   `python -m scripts.load_listings path/to/vehicles.csv`

Without `DATABASE_URL` the app still runs; failure curves and price check are just empty.

### 3. Frontend (Node 18+)
```bash
cd frontend
npm install
cp .env.example .env        # leave VITE_API_URL blank to work from sample data
npm run dev
```
Open http://localhost:5173. Test on your phone with `npm run dev -- --host` and your laptop's IP.

### Who works where
| Lane | Files |
| --- | --- |
| Lead, frontend + pitch | `frontend/src/` |
| Backend + data | `backend/app/nhtsa.py`, `backend/app/db.py`, `backend/scripts/`, `backend/db/` |
| AI | `backend/app/llm.py` (prompt, VIN photo) |

The contract between lanes is the report JSON: `shared/sample-report.json`. Change it only after telling the team.

## Deploy
- Frontend: Vercel or Netlify (root `frontend`, build `npm run build`, output `dist`, set `VITE_API_URL`). Turn analytics off.
- Backend: Render web service (root `backend`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`). Set the `.env` values and add the frontend URL to `ALLOWED_ORIGINS`.

## Tech stack
React, Vite, vite-plugin-pwa, FastAPI, Tiger Data (TimescaleDB), Google Gemini API, NHTSA APIs.

## Data sources
- NHTSA vPIC, Recalls, and Complaints APIs and the NHTSA complaints flat file (public, U.S. government)
- Craigslist used-cars dataset on Kaggle (public; listings from about spring 2021)

## Made before Hacklanta
- The datasets above (public).
- [List any starter template here.]

## Team
- Chris Miranda: lead, frontend, pitch
- [Name]: backend + data
- [Name]: AI

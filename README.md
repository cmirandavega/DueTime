# DueTime

Know what your car needs before it breaks. Skipped services, safety recalls, known failures at your mileage, and a fair private-sale price for any used car, in English and Spanish.

Built at **Hacklanta 2026** · Main track: **Social Good, presented by Cox Automotive**.

> The right to repair starts with the right to know what your car needs.

## Try it
- **Live app:** https://due-time.vercel.app
- **Demo video:** https://youtu.be/kOvqDF9IUFU

> The backend runs on a free server that sleeps when idle. The first load may take 30–50 seconds while it wakes up.

Tap a demo car to see it in action:
- **'01 Integra:** own mode. The "Has this been done?" checklist flags the overdue transmission service.
- **'13 Altima:** buying mode. Known problems, a pre-purchase checklist, and a price check on a $4,500 listing.
- **'04 330Ci:** fix-it-yourself vs. shop cards.

## Why we built it
My dad taught me and my brothers to take care of cars so they last a lifetime. When his 2001 Integra became mine, I kept up the engine but skipped the transmission service, and it cost me his car. Many students and commuters depend on one car they can't afford to replace, and nobody tells them what's due. DueTime does.

## Features
- **Has this been done?** Services due by your mileage, ranked by what skipping them can cost. Check off what's done, add roughly when, and it goes into your service log.
- **Safety recalls** from NHTSA, in plain language.
- **Known problems** for your exact car from NHTSA owner complaints, with the mileage range where owners report each failure.
- **Maintenance due now** and **fix it yourself or go to a shop?** cards: difficulty, tools, time, parts vs. shop cost.
- **Buying mode:** pre-purchase checklist, questions for the seller, and a price check against 363,899 real private-sale listings.
- **VIN photo scan:** photograph the VIN sticker and the car fills in.
- **Service log** you export to your own device.
- **English / Español** across the whole app.
- **Installable PWA:** works from a link or QR code on any phone.

## How it works
```
phone (PWA, Vercel) ──► FastAPI (Render) ──► NHTSA vPIC / Recalls / Complaints (public APIs)
                                 ├─────────► Tiger Data: price comps + failure mileage (public data only)
                                 ├─────────► Gemini: plain-language report, Spanish, VIN photo reading
                                 └─────────► Groq: backup when Gemini is unavailable
```
**Numbers come from data; words come from Gemini.** The prompt forbids inventing recalls, complaint counts, mileages, or prices. If every AI model is down, the app still shows the raw safety data instead of a blank screen. Finished demo reports are cached.

### Tiger Data
- `listings` hypertable: 363,899 cleaned Craigslist listings. Price comps use `percentile_cont`; `time_bucket` gives price trends.
- `complaints` hypertable: NHTSA owner complaints with mileage at failure (the NHTSA API doesn't expose mileage, so we load NHTSA's raw complaints file). For each component we compute the 25th–75th percentile failure mileage and flag your car when it falls inside that range.

## Privacy (Zero Data)
- No accounts, cookies, analytics, or tracking.
- The API never logs VINs or lookups (uvicorn runs with `--no-access-log`).
- VIN photos are processed in memory and never saved.
- The service log lives only on the user's screen; they export it to their own device.
- The database holds public car data only. Craigslist seller fields (URL, VIN, location, description) are dropped on import.
- To build a report, car details (and VIN photos) are sent to NHTSA and Google Gemini, which process them under their own privacy policies. We don't store them.
- Recent reports are cached only in your own browser for offline use; clearing site data removes them.

## Side challenges
- **Shock Tracker: Zero Data:** no accounts, tracking, profiles, or stored personal info (see Privacy).
- **MLH: Best Use of Gemini API:** Gemini writes every report in plain English or Spanish from real NHTSA and Tiger Data numbers, and reads VINs from phone photos.
- **Mercedes: Best Application of Computer Vision:** photograph a VIN sticker and DueTime reads and decodes it.

---

## Run it locally

### Backend (Python 3.11+)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # add GEMINI_API_KEY and DATABASE_URL (Groq optional)
python -m scripts.cache_demo_cars  # caches NHTSA data for the 3 demo cars
python -m uvicorn app.main:app --reload --no-access-log
```
API docs: http://localhost:8000/docs

### Database (Tiger Data)
1. Create a free service on Tiger Cloud and put its connection string in `DATABASE_URL`. If the password has special characters, URL-encode them or use letters and numbers only.
2. Run `backend/db/schema.sql` in the Tiger Cloud SQL Editor (or `psql "$DATABASE_URL" -f db/schema.sql`).
3. Complaints: download `FLAT_CMPL.zip` from https://www.nhtsa.gov/nhtsa-datasets-and-apis, unzip, then
   `python -m scripts.load_complaints path/to/FLAT_CMPL.txt` (demo cars only; add `--all` for everything).
4. Listings: download `vehicles.csv` from https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data, then
   `python -m scripts.load_listings path/to/vehicles.csv`.

Without `DATABASE_URL` the app still runs; the price check and failure ranges are just empty.

### Frontend (Node 18+)
```bash
cd frontend
npm install
cp .env.example .env               # VITE_API_URL=http://localhost:8000 (blank = sample data)
npm run dev
```
Open http://localhost:5173.

## Deploy
- **Frontend (Vercel):** root `frontend`, framework Vite, env `VITE_API_URL` = backend URL. Keep Analytics and Speed Insights off.
- **Backend (Render):** root `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`. Set the `.env` values as environment variables. Any `*.vercel.app` origin is allowed by CORS.

## Tech stack
React, Vite, vite-plugin-pwa, Python, FastAPI, Tiger Data (TimescaleDB / PostgreSQL), Google Gemini API, Groq, Pillow, NHTSA APIs, Vercel, Render.

## Data sources
- NHTSA vPIC, Recalls, and Complaints APIs and the NHTSA complaints flat file (public, U.S. government)
- Craigslist used-cars dataset on Kaggle (public; listings from about spring 2021, so prices are 2021 private-sale prices)

## Made before Hacklanta / disclosure
- The public datasets above, and the open-source libraries in `requirements.txt` and `package.json`.
- No starter template. We used Claude (Anthropic) to help plan the project and scaffold the starter code during the event; all design decisions, integration, data work, debugging, and the demo were done by our team.

## What's next
- "What's wrong with my car?": describe a symptom and get likely causes with web sources (Gemini + Google Search grounding; prototyped this weekend).
- A community where experienced DIYers answer model-specific questions.
- "Is this quote fair?": compare a shop's quote to typical parts and labor.
- SMS access for drivers without a data plan.

## Team
- **Chris Miranda** (team lead)
- **Taurus Gamble**
- **Kameron Ray**

We built DueTime together: pairing on one machine when we could, and splitting off branches for features when someone else was busy.

"""DueTime API.

Zero Data: no accounts, no cookies, no analytics, no request logging.
Run uvicorn with --no-access-log so VINs never land in server logs.
"""
import asyncio
import json
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import db, llm, nhtsa
from .config import ALLOWED_ORIGINS, DEMO_CACHE_DIR, DEMO_MODE

app = FastAPI(title="DueTime API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DISCLAIMERS = {
    "en": ["Costs and difficulty are estimates, not quotes.",
           "Brakes, airbags, and fuel lines: have a professional check your work."],
    "es": ["Los costos y la dificultad son estimados, no cotizaciones.",
           "Frenos, bolsas de aire y líneas de combustible: que un profesional revise tu trabajo."],
}


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/vin/{vin}")
async def vin(vin: str):
    vin = vin.strip().upper()
    if len(vin) != 17:
        raise HTTPException(400, "A VIN has 17 characters.")
    return await nhtsa.decode_vin(vin)


@app.post("/api/vin-photo")
async def vin_photo(photo: UploadFile = File(...)):
    data = await photo.read()  # kept in memory only, never written anywhere
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, "Photo too large (8 MB max).")
    try:
        found = await llm.read_vin_photo(data, photo.content_type or "image/jpeg")
    except Exception as e:
        print(f"VIN photo failed: {type(e).__name__}: {e}")
        raise HTTPException(422, "Couldn't read that photo. Try a JPG or PNG, closer to the VIN.")
    if not found:
        raise HTTPException(422, "Couldn't read a VIN. Try a closer, sharper photo.")
    return await nhtsa.decode_vin(found)


class DiagnoseIn(BaseModel):
    year: int = Field(..., ge=1950, le=2030)
    make: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    mileage: int | None = Field(None, ge=0, le=1_000_000)
    symptom: str = Field(..., min_length=3, max_length=500)
    lang: Literal["en", "es"] = "en"


@app.post("/api/diagnose")
async def diagnose(body: DiagnoseIn):
    """POST so the symptom text stays out of URLs and server logs."""
    make, model = body.make.strip().upper(), body.model.strip().upper()
    vehicle = {"year": body.year, "make": make, "model": model, "mileage": body.mileage}
    complaints = await nhtsa.complaints_summary(body.year, make, model)
    components = [c["component"] for c in complaints["by_component"]]
    try:
        result = await llm.diagnose(vehicle, body.symptom.strip(), body.lang, components)
    except Exception as e:
        print(f"Diagnose failed: {type(e).__name__}: {e}")
        raise HTTPException(503, "Search is busy right now. Try again in a minute.")
    counts = {c["component"]: c["count"] for c in complaints["by_component"]}
    for cause in result.get("causes", []):
        cause["nhtsa_complaints"] = counts.get(cause.get("nhtsa_component"))
    result["vehicle"] = vehicle
    return result


# Finished reports, keyed by the CAR (never by a person). Public data only.
_report_cache: dict[tuple, dict] = {}


def _report_path(key: tuple):
    name = "report_" + "_".join(str(k) for k in key).lower().replace(" ", "-") + ".json"
    return DEMO_CACHE_DIR / name


@app.get("/api/report")
async def report(
    year: int = Query(..., ge=1950, le=2030),
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    mileage: int | None = Query(None, ge=0, le=1_000_000),
    asking_price: int | None = Query(None, ge=0),
    mode: Literal["own", "buy"] = "own",
    lang: Literal["en", "es"] = "en",
    vin: str | None = None,
):
    make, model = make.strip().upper(), model.strip().upper()
    key = (year, make, model, mileage, asking_price, mode, lang)
    if key in _report_cache:
        return _report_cache[key]
    path = _report_path(key)
    if DEMO_MODE and path.exists():
        _report_cache[key] = json.loads(path.read_text(encoding="utf-8"))
        return _report_cache[key]

    vehicle = {"vin": None, "year": year, "make": make, "model": model, "mileage": mileage}

    recalls, complaints_api, curves, price = await asyncio.gather(
        nhtsa.recalls(year, make, model),
        nhtsa.complaints_summary(year, make, model),
        db.failure_curves(year, make, model, mileage),
        db.price_check(year, make, model, mileage, asking_price),
    )

    written = await llm.write_report(vehicle, mode, lang, recalls, complaints_api, curves, price)

    # Numbers come from data, words come from Gemini: merge by component.
    explanations = {p.get("component"): p.get("explanation", "") for p in written.get("known_problems", [])}
    source = curves if curves else [
        {"component": c["component"], "complaint_count": c["count"]} for c in complaints_api["by_component"]
    ]
    known_problems = [{
        "component": p["component"],
        "complaint_count": p.get("complaint_count"),
        "typical_mileage": {k: p.get(k) for k in ("p25", "median", "p75")} if curves else None,
        "in_range": p.get("in_range"),
        "explanation": explanations.get(p["component"], ""),
    } for p in source]

    result = {
        "vehicle": vehicle,
        "mode": mode,
        "language": lang,
        "summary": written.get("summary", ""),
        "recalls": written.get("recalls", []),
        "known_problems": known_problems,
        "maintenance_due": written.get("maintenance_due", []),
        "declined_services": written.get("declined_services", []),
        "diy_cards": written.get("diy_cards", []),
        "pre_purchase": written.get("pre_purchase", {"inspect": [], "should_be_done": [], "ask_seller": []}),
        "price_check": price or {"asking_price": asking_price, "comps": 0, "verdict": "not_enough_data", "trend": []},
        "sources": ["NHTSA vPIC", "NHTSA Recalls", "NHTSA Complaints", "Craigslist used cars (Kaggle)"],
        "disclaimers": DISCLAIMERS[lang],
    }

    # Only keep real AI output; the no-AI fallback is retried next time.
    if not written.get("_fallback"):
        _report_cache[key] = result
        if DEMO_MODE:
            path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result

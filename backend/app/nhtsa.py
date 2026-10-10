"""NHTSA public APIs (free, no key) with a small on-disk cache for the demo cars.

Zero Data: nothing here logs VINs or lookups. The cache only ever holds the
public NHTSA responses for the demo cars, written by scripts/cache_demo_cars.py.
"""
import json
from collections import Counter

import httpx

from .config import DEMO_CACHE_DIR, DEMO_MODE

VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle"
COMPLAINTS = "https://api.nhtsa.gov/complaints/complaintsByVehicle"

TIMEOUT = httpx.Timeout(15.0)


def cache_key(kind: str, year: int, make: str, model: str) -> str:
    return f"{year}_{make}_{model}_{kind}".lower().replace(" ", "-") + ".json"


def read_cache(kind: str, year: int, make: str, model: str):
    path = DEMO_CACHE_DIR / cache_key(kind, year, make, model)
    if DEMO_MODE and path.exists():
        return json.loads(path.read_text())
    return None


async def decode_vin(vin: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(VPIC.format(vin=vin))
        r.raise_for_status()
    row = (r.json().get("Results") or [{}])[0]
    year = row.get("ModelYear")
    return {
        "vin": vin,
        "year": int(year) if year and year.isdigit() else None,
        "make": (row.get("Make") or "").upper() or None,
        "model": (row.get("Model") or "").upper() or None,
        "trim": row.get("Trim") or None,
        "error": row.get("ErrorText") if row.get("ErrorCode") not in (None, "0") else None,
    }


async def _get(url: str, kind: str, year: int, make: str, model: str) -> dict:
    cached = read_cache(kind, year, make, model)
    if cached is not None:
        return cached
    params = {"make": make, "model": model, "modelYear": year}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
    return r.json()


async def recalls(year: int, make: str, model: str) -> list[dict]:
    data = await _get(RECALLS, "recalls", year, make, model)
    return [
        {
            "campaign": x.get("NHTSACampaignNumber"),
            "component": x.get("Component"),
            "summary": x.get("Summary"),
            "consequence": x.get("Consequence"),
            "remedy": x.get("Remedy"),
            "park_it": bool(x.get("parkIt")),
        }
        for x in data.get("results", [])
    ]


async def complaints_summary(year: int, make: str, model: str, top: int = 6) -> dict:
    """Complaint counts by component from the API.

    The API has no mileage field. Mileage-at-failure comes from the complaints
    flat file loaded into Tiger Data (see db.py and scripts/load_complaints.py).
    """
    data = await _get(COMPLAINTS, "complaints", year, make, model)
    results = data.get("results", [])
    counts = Counter()
    for c in results:
        for comp in (c.get("components") or "").split(","):
            comp = comp.strip()
            if comp:
                counts[comp] += 1
    return {
        "total": len(results),
        "by_component": [{"component": k, "count": v} for k, v in counts.most_common(top)],
    }

"""Save NHTSA recalls + complaints for the demo cars into demo_cache/.

Run tonight, from the backend folder:
    python -m scripts.cache_demo_cars

If a car shows 0 recalls AND 0 complaints, NHTSA probably names the model
differently (e.g. "3 SERIES" vs "330CI"). Fix demo_cars.json and rerun.
"""
import asyncio
import json
from pathlib import Path

import httpx

from app.config import DEMO_CACHE_DIR
from app.nhtsa import COMPLAINTS, RECALLS, cache_key

CARS = json.loads((Path(__file__).parent / "demo_cars.json").read_text())


async def main():
    DEMO_CACHE_DIR.mkdir(exist_ok=True)
    async with httpx.AsyncClient(timeout=30) as client:
        for car in CARS:
            params = {"make": car["make"], "model": car["model"], "modelYear": car["year"]}
            for kind, url in (("recalls", RECALLS), ("complaints", COMPLAINTS)):
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
                path = DEMO_CACHE_DIR / cache_key(kind, car["year"], car["make"], car["model"])
                path.write_text(json.dumps(data, indent=1))
                n = len(data.get("results", []))
                print(f"{car['year']} {car['make']} {car['model']:<8} {kind:<10} {n:>4}  -> {path.name}")


if __name__ == "__main__":
    asyncio.run(main())

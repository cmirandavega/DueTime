"""Load the Kaggle Craigslist used-cars dataset into Tiger Data.

1. Download vehicles.csv from https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data
2. From the backend folder:
       python -m scripts.load_listings path/to/vehicles.csv

Only price, year, make, model, odometer, condition, state, and posting date are kept.
Seller-identifying fields (url, VIN, lat/long, description, images) are dropped.
Note: listings were scraped over a short window (about spring 2021), so the
monthly trend is short. Prices are 2021 private-sale prices; say so in the demo.
"""
import argparse
import csv
import sys
from datetime import datetime

import psycopg

from app.config import DATABASE_URL

csv.field_size_limit(sys.maxsize)


def to_int(s: str) -> int | None:
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


def rows(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            price, year = to_int(r.get("price")), to_int(r.get("year"))
            make = (r.get("manufacturer") or "").strip().lower()
            model = (r.get("model") or "").strip().lower()
            posted = (r.get("posting_date") or "").strip()

            # 1. Skip rows missing anything we need
            if not (price and year and make and model and posted):
                continue
            # 2. Skip junk: fake prices, bad years
            if not (500 <= price <= 200_000) or not (1950 <= year <= 2025):
                continue
            # 3. Impossible mileage -> unknown
            odo = to_int(r.get("odometer"))
            if odo is not None and not (0 <= odo <= 1_000_000):
                odo = None

            try:
                posted_at = datetime.strptime(posted, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                continue
            yield (posted_at, make, model, year, odo, price,
                   (r.get("condition") or None), (r.get("state") or None))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    if not DATABASE_URL:
        raise SystemExit("Set DATABASE_URL in backend/.env first.")
    n = 0
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        with cur.copy("COPY listings (posted_at, make, model, model_year, odometer, price, condition, state) "
                      "FROM STDIN") as copy:
            for r in rows(args.path):
                copy.write_row(r)
                n += 1
    print(f"Loaded {n} listings.")


if __name__ == "__main__":
    main()

"""Load NHTSA complaints (with mileage at failure) into Tiger Data.

1. Download a complaints file from https://www.nhtsa.gov/nhtsa-datasets-and-apis
   (FLAT_CMPL.zip = everything, or COMPLAINTS_RECEIVED_YYYY-YYYY.zip chunks) and unzip it.
2. From the backend folder:
       python -m scripts.load_complaints path/to/FLAT_CMPL.txt
   Add --all to load every vehicle instead of only the demo cars' make/model.

Field layout (tab-delimited, no header): https://static.nhtsa.gov/odi/ffdd/cmpl/CMPL.txt
"""
import argparse
import json
from datetime import date
from pathlib import Path

import psycopg

from app.config import DATABASE_URL

# 0-based column positions from CMPL.txt
ODINO, MAKETXT, MODELTXT, YEARTXT, CRASH, FAILDATE, FIRE, COMPDESC, DATEA, MILES = 1, 3, 4, 5, 6, 7, 8, 11, 15, 17

CARS = json.loads((Path(__file__).parent / "demo_cars.json").read_text())


def ymd(s: str) -> date | None:
    s = s.strip()
    if len(s) != 8 or not s.isdigit() or s == "00000000":
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    except ValueError:
        return None


def rows(path: str, load_all: bool):
    wanted = {(c["make"].upper(), c["model"].upper()) for c in CARS}
    with open(path, encoding="latin-1") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) <= MILES:
                continue
            make, model = p[MAKETXT].strip().upper(), p[MODELTXT].strip().upper()
            if not load_all and (make, model) not in wanted:
                continue
            year, added = p[YEARTXT].strip(), ymd(p[DATEA])
            if not year.isdigit() or year == "9999" or added is None:
                continue
            miles = p[MILES].strip()
            yield (
                int(p[ODINO]), make, model, int(year), p[COMPDESC].strip() or "UNKNOWN",
                int(miles) if miles.isdigit() and int(miles) > 0 else None,
                ymd(p[FAILDATE]), added, p[CRASH].strip() == "Y", p[FIRE].strip() == "Y",
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if not DATABASE_URL:
        raise SystemExit("Set DATABASE_URL in backend/.env first.")
    n = 0
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        with cur.copy("COPY complaints (odino, make, model, model_year, component, miles, "
                      "fail_date, date_added, crash, fire) FROM STDIN") as copy:
            for r in rows(args.path, args.all):
                copy.write_row(r)
                n += 1
    print(f"Loaded {n} complaint rows.")


if __name__ == "__main__":
    main()

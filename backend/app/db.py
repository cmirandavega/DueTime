"""Tiger Data (TimescaleDB on Postgres) queries.

The database holds PUBLIC car data only: NHTSA complaints and anonymized
Craigslist listings. No user data is ever written here.
If DATABASE_URL is empty, every function returns None and the app still runs.
"""
import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL


async def _fetch(sql: str, params: dict) -> list[dict] | None:
    if not DATABASE_URL:
        return None
    async with await psycopg.AsyncConnection.connect(DATABASE_URL, row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


FAILURE_CURVES = """
SELECT component,
       count(*)                                                  AS complaint_count,
       percentile_cont(0.25) WITHIN GROUP (ORDER BY miles)::int  AS p25,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY miles)::int  AS median,
       percentile_cont(0.75) WITHIN GROUP (ORDER BY miles)::int  AS p75
FROM complaints
WHERE make = %(make)s AND model = %(model)s
  AND model_year BETWEEN %(year)s - %(span)s AND %(year)s + %(span)s
  AND miles > 0
GROUP BY component
HAVING count(*) >= %(min_n)s
ORDER BY complaint_count DESC
LIMIT %(limit)s
"""


async def failure_curves(year: int, make: str, model: str, mileage: int | None,
                         span: int = 1, min_n: int = 3, limit: int = 6) -> list[dict] | None:
    rows = await _fetch(FAILURE_CURVES, {
        "make": make.upper(), "model": model.upper(), "year": year,
        "span": span, "min_n": min_n, "limit": limit,
    })
    if rows is None:
        return None
    for r in rows:
        r["in_range"] = bool(mileage and r["p25"] is not None and r["p25"] <= mileage <= r["p75"])
    return rows


COMPS_FILTER = """
FROM listings
WHERE make = %(make)s
  AND model LIKE %(model_like)s
  AND model_year BETWEEN %(year)s - 1 AND %(year)s + 1
  AND odometer BETWEEN %(lo)s AND %(hi)s
  AND price BETWEEN 500 AND 200000
"""

COMPS_STATS = """
SELECT count(*)                                                   AS comps,
       percentile_cont(0.25) WITHIN GROUP (ORDER BY price)::int   AS p25,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY price)::int   AS median,
       percentile_cont(0.75) WITHIN GROUP (ORDER BY price)::int   AS p75
""" + COMPS_FILTER

# time_bucket is TimescaleDB: median comp price per month
COMPS_TREND = """
SELECT time_bucket('1 month', posted_at)::date                    AS month,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY price)::int    AS median,
       count(*)                                                    AS n
""" + COMPS_FILTER + """
GROUP BY month
ORDER BY month
"""


def verdict(asking: int | None, stats: dict) -> str:
    if not stats or (stats.get("comps") or 0) < 5:
        return "not_enough_data"
    if asking is None:
        return "unknown"
    if asking < stats["p25"] * 0.7:
        return "suspiciously_low"
    if asking < stats["p25"]:
        return "below_market"
    if asking > stats["p75"]:
        return "high"
    return "fair"


async def price_check(year: int, make: str, model: str, mileage: int | None,
                      asking: int | None) -> dict | None:
    miles = mileage or 0
    params = {
        "make": make.lower(),
        "model_like": "%" + model.lower() + "%",
        "year": year,
        "lo": int(miles * 0.75),
        "hi": int(miles * 1.25) if miles else 10_000_000,
    }
    stats = await _fetch(COMPS_STATS, params)
    if stats is None:
        return None
    s = stats[0] if stats else {}
    trend = await _fetch(COMPS_TREND, params) or []
    return {
        "asking_price": asking,
        "comps": s.get("comps", 0),
        "p25": s.get("p25"),
        "median": s.get("median"),
        "p75": s.get("p75"),
        "verdict": verdict(asking, s),
        "trend": [{"month": str(t["month"]), "median": t["median"], "n": t["n"]} for t in trend],
    }

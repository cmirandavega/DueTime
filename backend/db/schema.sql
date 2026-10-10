-- DueTime on Tiger Data (TimescaleDB). Public car data only; no user data.
-- Run once: psql "$DATABASE_URL" -f backend/db/schema.sql

-- NHTSA owner complaints (from the complaints flat file, which has mileage at failure).
-- One row per complaint component.
CREATE TABLE IF NOT EXISTS complaints (
    odino        BIGINT      NOT NULL,
    make         TEXT        NOT NULL,
    model        TEXT        NOT NULL,
    model_year   INT         NOT NULL,
    component    TEXT        NOT NULL,
    miles        INT,
    fail_date    DATE,
    date_added   DATE        NOT NULL,
    crash        BOOLEAN,
    fire         BOOLEAN
);
SELECT create_hypertable('complaints', by_range('date_added'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS complaints_vehicle_idx ON complaints (make, model, model_year, date_added DESC);

-- Private-sale listings from the Kaggle Craigslist used-cars dataset.
-- Seller-identifying columns (url, VIN, lat/long, description, images) are NOT loaded.
CREATE TABLE IF NOT EXISTS listings (
    posted_at    TIMESTAMPTZ NOT NULL,
    make         TEXT        NOT NULL,
    model        TEXT        NOT NULL,
    model_year   INT         NOT NULL,
    odometer     INT,
    price        INT         NOT NULL,
    condition    TEXT,
    state        TEXT
);
SELECT create_hypertable('listings', by_range('posted_at'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS listings_vehicle_idx ON listings (make, model, model_year, posted_at DESC);

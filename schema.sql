CREATE TABLE IF NOT EXISTS deals (
    pipedrive_id    INTEGER PRIMARY KEY,
    title           TEXT,
    org_name        TEXT,
    value           NUMERIC(15,2),
    currency        VARCHAR(10),
    status          VARCHAR(20),
    product         TEXT,
    platform        TEXT,
    revenue_type    TEXT,
    asset_assigned  TEXT,
    book_value      NUMERIC(15,2),
    end_of_lease    DATE,
    lease_fee       NUMERIC(15,2),
    monthly_costs   NUMERIC(15,2),
    close_date      TIMESTAMPTZ,
    stage_id        INTEGER,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deal_products (
    id              SERIAL PRIMARY KEY,
    deal_id         INTEGER NOT NULL REFERENCES deals(pipedrive_id) ON DELETE CASCADE,
    product_name    TEXT,
    quantity        NUMERIC(10,2),
    unit_price      NUMERIC(15,2),
    total_price     NUMERIC(15,2),
    currency        VARCHAR(10),
    UNIQUE (deal_id, product_name)
);

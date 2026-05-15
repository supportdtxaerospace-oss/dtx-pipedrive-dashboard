import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("PIPEDRIVE_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

PIPELINE_ID = 3  # DTX LDG

FIELD_KEYS = {
    "asset":        "ead197471c387e3e2c663538e90152cc35bc2163",
    "book_value":   "177db171517682d3f1113f92577d1103dad5c511",
    "end_of_lease": "b2039b5aea220c518b14344366b763f471ff19f2",
    "lease_fee":    "1c471535fcda442a329cd43e9b5e16b951e65db5",
    "monthly_costs":"8298781efc2480e2f3bc8f7d4761c750a272b58a",
    "product":      "1ddc595d95a5b44f70f7276bcba37d1d3877d088",
    "platform":     "4695ff24a507815d2c8f043760de6f7d79b247b4",
    "revenue_type": "e2890dfc357f253753d878be50223e0faeedc6d0",
}

PRODUCT_LABELS = {27: "ENGINE", 28: "LDG", 29: "AIRFRAME", 30: "MRO", 55: "APU"}

PLATFORM_LABELS = {
    60: "A320 CEO", 61: "A321 CEO", 62: "A320 NEO", 63: "A321 NEO",
    64: "A330",    65: "A340",     66: "A380",
    67: "737 CL",  68: "737 NG",   69: "737 MAX",
    70: "757",     71: "767",      72: "777",     73: "787",
    74: "ATR",     75: "ERJ",
}

REVENUE_TYPE_LABELS = {
    80: "Sales - Landing Gear",   81: "Sales - Engine",       82: "Sales - APU",
    83: "Lease - Landing Gear",   84: "Lease - Engine",       85: "Lease - APU",
    86: "Exchange - Landing Gear",87: "Exchange - Engine",    88: "Exchange - APU",
    89: "APU Sublease",           90: "APU Brokering",        91: "APU Repair",
    92: "LDG Sublease",           93: "LDG Brokering",
    94: "Airframe Purchase",      95: "Airframe Sale",
}


def resolve_set(value, labels):
    if not value:
        return None
    ids = [int(x) for x in str(value).split(",") if x.strip().isdigit()]
    return ", ".join(labels.get(i, str(i)) for i in ids)


def resolve_enum(value, labels):
    if not value:
        return None
    try:
        return labels.get(int(value), str(value))
    except (ValueError, TypeError):
        return str(value)


def fetch_by_status(status):
    deals, start = [], 0
    while True:
        resp = requests.get(
            "https://api.pipedrive.com/v1/deals",
            params={
                "api_token": TOKEN,
                "pipeline_id": PIPELINE_ID,
                "status": status,
                "limit": 100,
                "start": start,
            },
        )
        data = resp.json()
        if not data.get("success") or not data.get("data"):
            break
        deals.extend(data["data"])
        pagination = data.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection"):
            break
        start += 100
    return deals


def fetch_all_deals():
    all_deals = []
    for status in ("open", "won", "lost"):
        batch = fetch_by_status(status)
        print(f"  {status}: {len(batch)} deals")
        all_deals.extend(batch)
    return [d for d in all_deals if d.get("pipeline_id") == PIPELINE_ID]


def fetch_deal_products(deal_id):
    resp = requests.get(
        f"https://api.pipedrive.com/v1/deals/{deal_id}/products",
        params={"api_token": TOKEN},
    )
    data = resp.json()
    if not data.get("success") or not data.get("data"):
        return []
    return data["data"]


def upsert_products(cur, deal_id, products):
    cur.execute("DELETE FROM deal_products WHERE deal_id = %s", (deal_id,))
    for p in products:
        cur.execute(
            """
            INSERT INTO deal_products (deal_id, product_name, quantity, unit_price, total_price, currency)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (deal_id, product_name) DO UPDATE SET
                quantity    = EXCLUDED.quantity,
                unit_price  = EXCLUDED.unit_price,
                total_price = EXCLUDED.total_price
            """,
            (
                deal_id,
                p.get("name"),
                p.get("quantity"),
                p.get("item_price"),
                p.get("sum"),
                p.get("currency"),
            ),
        )


def upsert_deal(cur, d):
    k = FIELD_KEYS
    cur.execute(
        """
        INSERT INTO deals (
            pipedrive_id, title, org_name, value, currency,
            status, product, platform, revenue_type,
            asset_assigned, book_value, end_of_lease,
            lease_fee, monthly_costs,
            close_date, stage_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (pipedrive_id) DO UPDATE SET
            title          = EXCLUDED.title,
            org_name       = EXCLUDED.org_name,
            value          = EXCLUDED.value,
            status         = EXCLUDED.status,
            product        = EXCLUDED.product,
            platform       = EXCLUDED.platform,
            revenue_type   = EXCLUDED.revenue_type,
            asset_assigned = EXCLUDED.asset_assigned,
            book_value     = EXCLUDED.book_value,
            end_of_lease   = EXCLUDED.end_of_lease,
            lease_fee      = EXCLUDED.lease_fee,
            monthly_costs  = EXCLUDED.monthly_costs,
            close_date     = EXCLUDED.close_date,
            synced_at      = NOW()
        """,
        (
            d["id"],
            d.get("title"),
            d["org_id"]["name"] if d.get("org_id") else None,
            d.get("value"),
            d.get("currency"),
            d.get("status"),
            resolve_set(d.get(k["product"]), PRODUCT_LABELS),
            resolve_set(d.get(k["platform"]), PLATFORM_LABELS),
            resolve_enum(d.get(k["revenue_type"]), REVENUE_TYPE_LABELS),
            d.get(k["asset"]),
            d.get(k["book_value"]),
            d.get(k["end_of_lease"]),
            d.get(k["lease_fee"]),
            d.get(k["monthly_costs"]),
            d.get("won_time") or d.get("close_time"),
            d.get("stage_id"),
        ),
    )


def main():
    print("Buscando deals do pipeline DTX LDG...")
    deals = fetch_all_deals()
    print(f"{len(deals)} deals encontrados.")

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for deal in deals:
        upsert_deal(cur, deal)
        products = fetch_deal_products(deal["id"])
        upsert_products(cur, deal["id"], products)

    conn.commit()
    cur.close()
    conn.close()
    print("Sincronização concluída!")


if __name__ == "__main__":
    main()

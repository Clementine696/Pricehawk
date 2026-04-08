#!/usr/bin/env python3
"""
Makro Price by Location Cron Job

For each product in monitored watchlists (with a verified Makro match),
fetches the Makro price at each monitored postal zone and stores it in
makro_location_prices.

Makro is location-dependent: price varies by delivery postal code.
The postal code is sent via the 'storeCode' cookie in the HTTP request.

Railway Cron Setup:
  Command:  python update_makro_location_prices.py
  Schedule: 0 3 * * *  (daily at 3 AM UTC = 10 AM Thailand)

Environment Variables:
- DATABASE_URL or DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD/DB_SSLMODE
- MAKRO_LOC_DELAY: Delay between requests in seconds (default: 1.0)
- MAKRO_LOC_TIMEOUT: HTTP timeout per request (default: 15)
"""

import os
import sys
import json
import time
import re
import logging
import urllib.request
import urllib.error
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _, _v = _line.partition('=')
                os.environ.setdefault(_k.strip(), _v.strip())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
def get_conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', 5432)),
            dbname=os.environ.get('DB_NAME', 'pricehawk'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', ''),
            sslmode=os.environ.get('DB_SSLMODE', 'prefer'),
            cursor_factory=RealDictCursor,
        )
    conn.autocommit = False
    return conn

# ---------------------------------------------------------------------------
# Fetch Makro price for a specific postal code
# ---------------------------------------------------------------------------
def fetch_makro_price_by_location(url: str, postal_code: str, timeout: int = 15) -> dict:
    """
    Fetch Makro product price for a specific postal/delivery zone.
    Makro uses the 'storeCode' cookie to determine the serving branch.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cookie": f"storeCode={postal_code}; selectedPostalCode={postal_code}",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not match:
        return {"success": False, "error": "__NEXT_DATA__ not found"}

    try:
        data = json.loads(match.group(1))
    except Exception as e:
        return {"success": False, "error": f"JSON parse: {e}"}

    p = data.get("props", {}).get("pageProps", {}).get("product")
    if not p:
        return {"success": False, "error": "product missing in pageProps"}

    current_price = None
    try:
        current_price = float(p.get("displayPrice") or 0) or None
    except (TypeError, ValueError):
        pass

    return {"success": True, "price": current_price}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 70)
    logger.info("  MAKRO PRICE BY LOCATION UPDATE")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    delay   = float(os.environ.get('MAKRO_LOC_DELAY', 1.0))
    timeout = int(os.environ.get('MAKRO_LOC_TIMEOUT', 15))

    conn = get_conn()
    cur = conn.cursor()

    # 1. Get monitored watchlists
    cur.execute("SELECT watchlist_id FROM pbl_monitored_watchlists")
    watchlist_ids = [r["watchlist_id"] for r in cur.fetchall()]
    if not watchlist_ids:
        logger.info("No monitored watchlists configured. Done.")
        conn.close()
        return 0
    logger.info(f"Monitored watchlists: {watchlist_ids}")

    # 2. Get monitored locations
    cur.execute("""
        SELECT ml.id as location_id, ml.name, ml.branch_code as postal_code
        FROM pbl_monitored_locations pml
        JOIN makro_locations ml ON pml.location_id = ml.id
        WHERE ml.is_active = TRUE
    """)
    locations = cur.fetchall()
    if not locations:
        logger.info("No monitored locations configured. Done.")
        conn.close()
        return 0
    logger.info(f"Monitored locations: {len(locations)}")

    # 3. Get all CFW products in monitored watchlists that have a verified Makro match
    placeholders = ','.join(['%s'] * len(watchlist_ids))
    cur.execute(f"""
        SELECT DISTINCT
            mp.id as makro_product_id,
            mp.sku as makro_sku,
            mp.name as makro_name,
            mp.url as makro_url
        FROM watchlist_products wp
        JOIN products cfw ON wp.product_id = cfw.id
        JOIN product_matches pm ON pm.cfw_product_id = cfw.id
            AND pm.is_verified = TRUE AND pm.is_same = TRUE
        JOIN products mp ON pm.makro_product_id = mp.id
        WHERE wp.watchlist_id IN ({placeholders})
          AND mp.url IS NOT NULL AND mp.url != ''
          AND mp.is_active = TRUE
    """, watchlist_ids)
    products = cur.fetchall()

    if not products:
        logger.info("No products found in monitored watchlists with verified Makro matches.")
        conn.close()
        return 0

    total_products = len(products)
    total_locations = len(locations)
    total_combinations = total_products * total_locations
    logger.info(f"Products: {total_products} × Locations: {total_locations} = {total_combinations} combinations")

    updated = 0
    failed = 0
    i = 0

    for product in products:
        makro_id  = product["makro_product_id"]
        makro_sku = product["makro_sku"]
        makro_url = product["makro_url"]

        for loc in locations:
            i += 1
            loc_id      = loc["location_id"]
            loc_name    = loc["name"]
            postal_code = loc["postal_code"]

            result = fetch_makro_price_by_location(makro_url, postal_code, timeout=timeout)

            if not result["success"]:
                failed += 1
                logger.warning(f"[{i}/{total_combinations}] FAIL {makro_sku} @ {postal_code} — {result['error']}")
            else:
                price = result["price"]
                try:
                    cur.execute("""
                        INSERT INTO makro_location_prices (makro_product_id, location_id, price, scraped_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (makro_product_id, location_id)
                        DO UPDATE SET price = EXCLUDED.price, scraped_at = NOW()
                    """, (makro_id, loc_id, price))
                    conn.commit()
                    updated += 1
                    logger.info(f"[{i}/{total_combinations}] OK   {makro_sku} @ {postal_code} ({loc_name}) → ฿{price}")
                except Exception as e:
                    conn.rollback()
                    failed += 1
                    logger.error(f"[{i}/{total_combinations}] DB ERROR {makro_sku} @ {postal_code}: {e}")

            if i < total_combinations:
                time.sleep(delay)

    cur.close()
    conn.close()

    logger.info("=" * 70)
    logger.info(f"  COMPLETE: {updated} updated, {failed} failed / {total_combinations} total")
    logger.info(f"  Finished: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    return 1 if failed > updated else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Makro Daily Price Update Cron Job

Fetches current prices for all active Makro products using plain HTTP
(no browser needed — Makro embeds all data in __NEXT_DATA__ JSON).

Railway Cron Setup:
1. Create new service in Railway
2. Set command: python update_makro_prices.py
3. Set schedule: 0 2 * * * (daily at 2 AM UTC = 9 AM Thailand)

Environment Variables:
- DATABASE_URL or DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD/DB_SSLMODE
- MAKRO_DELAY: Delay between requests in seconds (default: 1.0)
- MAKRO_LIMIT: Optional limit on number of products (default: all)
- MAKRO_BATCH_SIZE: Products per batch before logging progress (default: 50)
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

# Load .env from backend directory
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _, _v = _line.partition('=')
                os.environ.setdefault(_k.strip(), _v.strip())

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
def get_db_connection():
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
# HTTP fetch Makro price (no browser)
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_makro_price(url: str, timeout: int = 15) -> dict:
    """Fetch Makro product data via plain HTTP. Returns dict with success/price/step_prices."""
    req = urllib.request.Request(url, headers=HEADERS)
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
        return {"success": False, "error": "product key missing in pageProps"}

    current_price = None
    try:
        current_price = float(p.get("displayPrice") or 0) or None
    except (TypeError, ValueError):
        pass

    # Step prices from slabPriceTiers
    step_prices = []
    slab_data = p.get("slabPrices")
    if slab_data and isinstance(slab_data, dict) and current_price:
        tiers = sorted(slab_data.get("slabPriceTiers") or [], key=lambda t: t.get("tier", 0))
        if tiers:
            step_prices = [[1, current_price]] + [
                [t["quantity"], float(t["priceInVat"])]
                for t in tiers
                if t.get("quantity") is not None and t.get("priceInVat") is not None
            ]

    images = p.get("imageUrls") or []

    return {
        "success": True,
        "current_price": current_price,
        "step_prices": step_prices,
        "image": images[0] if images else None,
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 70)
    logger.info("  MAKRO DAILY PRICE UPDATE")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    delay       = float(os.environ.get('MAKRO_DELAY', 1.0))
    limit_str   = os.environ.get('MAKRO_LIMIT')
    limit       = int(limit_str) if limit_str else None
    batch_size  = int(os.environ.get('MAKRO_BATCH_SIZE', 50))

    logger.info(f"Config: delay={delay}s  limit={limit or 'ALL'}  batch_size={batch_size}")

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all active Makro products that have a URL
    query = """
        SELECT id, sku, name, url, current_price
        FROM products
        WHERE retailer_id = 'makro'
          AND is_active = TRUE
          AND url IS NOT NULL AND url != ''
        ORDER BY updated_at ASC
    """
    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    products = cur.fetchall()

    total = len(products)
    logger.info(f"Found {total} Makro products to update")

    updated = 0
    failed = 0
    skipped = 0
    errors = []

    for i, product in enumerate(products, 1):
        pid   = product["id"]
        sku   = product["sku"]
        url   = product["url"]
        old_price = product["current_price"]

        result = fetch_makro_price(url)

        if not result["success"]:
            failed += 1
            err_msg = f"SKU {sku}: {result['error']}"
            errors.append(err_msg)
            logger.warning(f"[{i}/{total}] FAIL {sku} — {result['error']}")
        else:
            new_price = result["current_price"]
            step_prices_json = json.dumps(result["step_prices"])
            image = result["image"]

            if new_price is None:
                skipped += 1
                logger.debug(f"[{i}/{total}] SKIP {sku} — no price extracted")
            else:
                try:
                    cur.execute("""
                        UPDATE products
                        SET current_price = %s,
                            step_prices   = %s,
                            image_url     = COALESCE(%s, image_url),
                            updated_at    = NOW()
                        WHERE id = %s
                    """, (new_price, step_prices_json, image, pid))

                    cur.execute("""
                        INSERT INTO price_history (product_id, price, step_prices)
                        VALUES (%s, %s, %s)
                    """, (pid, new_price, step_prices_json))

                    conn.commit()
                    updated += 1

                    price_change = ""
                    if old_price and new_price != float(old_price):
                        diff = new_price - float(old_price)
                        price_change = f" (was ฿{old_price} → ฿{new_price}, {'+' if diff > 0 else ''}{diff:.2f})"
                    logger.info(f"[{i}/{total}] OK   {sku}{price_change}")
                except Exception as e:
                    conn.rollback()
                    failed += 1
                    logger.error(f"[{i}/{total}] DB ERROR {sku}: {e}")

        # Progress log every batch_size
        if i % batch_size == 0:
            logger.info(f"--- Progress: {i}/{total} | updated={updated} failed={failed} skipped={skipped} ---")

        if i < total:
            time.sleep(delay)

    cur.close()
    conn.close()

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info(f"  MAKRO PRICE UPDATE COMPLETE")
    logger.info(f"  Finished:  {datetime.now().isoformat()}")
    logger.info(f"  Total:     {total}")
    logger.info(f"  Updated:   {updated}")
    logger.info(f"  Skipped:   {skipped}")
    logger.info(f"  Failed:    {failed}")
    logger.info("=" * 70)

    if errors:
        logger.warning(f"Failed URLs ({len(errors)}):")
        for e in errors[:20]:
            logger.warning(f"  {e}")

    # Save summary JSON
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "config": {"delay": delay, "limit": limit, "batch_size": batch_size},
        "errors": errors[:50],
    }
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "makro_updates")
    os.makedirs(results_dir, exist_ok=True)
    summary_file = os.path.join(results_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info(f"Summary saved: {summary_file}")

    failure_rate = (failed / total * 100) if total > 0 else 0
    if failure_rate > 30:
        logger.warning(f"HIGH FAILURE RATE: {failure_rate:.1f}% — check network/Makro site changes")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

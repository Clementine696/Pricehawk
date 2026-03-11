"""
Test Location Price Updater for Specific SKU

Tests location-based price scraping for a single Thai Watsadu SKU
across all monitored locations.

Usage:
    python test_location_update_sku.py <TWD_SKU>           # Update specific SKU
    python test_location_update_sku.py <TWD_SKU> --dry-run # Test without DB update
    python test_location_update_sku.py 60311766            # Example: MEX oven

Example:
    python test_location_update_sku.py 60293805
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

from database import get_db
from location_price_updater import LocationPriceUpdater


def get_gbh_product_for_sku(twd_sku: str):
    """
    Get GlobalHouse product that matches the given Thai Watsadu SKU.
    
    Returns:
        Dict with gbh_product_id, gbh_sku, gbh_name, gbh_link, twd_sku, twd_name
        or None if no match found
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT
                    p_gbh.product_id as gbh_product_id,
                    p_gbh.sku as gbh_sku,
                    p_gbh.name as gbh_name,
                    p_gbh.link as gbh_link,
                    p_gbh.current_price as gbh_current_price,
                    p_twd.product_id as twd_product_id,
                    p_twd.sku as twd_sku,
                    p_twd.name as twd_name,
                    p_twd.current_price as twd_current_price
                FROM products p_twd
                JOIN product_matches pm ON pm.base_product_id = p_twd.product_id
                    AND pm.verified_by_user = TRUE
                    AND pm.is_same = TRUE
                JOIN products p_gbh ON pm.candidate_product_id = p_gbh.product_id
                    AND p_gbh.retailer_id = 'gbh'
                WHERE p_twd.retailer_id = 'twd'
                    AND p_twd.sku = %s
                    AND p_gbh.link IS NOT NULL
                    AND p_gbh.link != ''
            """, (twd_sku,))
            
            result = cur.fetchone()
            return dict(result) if result else None


def get_monitored_locations():
    """Get all monitored locations."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    l.location_id,
                    l.retailer_id,
                    l.name_th,
                    l.name_en,
                    l.branch_code
                FROM location_monitored_locations lml
                JOIN locations l ON lml.location_id = l.location_id
                WHERE l.retailer_id = 'gbh'
                ORDER BY l.location_id
            """)
            return [dict(row) for row in cur.fetchall()]


def main():
    parser = argparse.ArgumentParser(
        description="Test location price update for a specific Thai Watsadu SKU"
    )
    parser.add_argument(
        "sku",
        help="Thai Watsadu SKU to test (e.g., 60293805)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test without updating database"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per scrape in seconds (default: 120)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80, flush=True)
    print("  LOCATION PRICE UPDATER - SINGLE SKU TEST", flush=True)
    print(f"  Thai Watsadu SKU: {args.sku}", flush=True)
    print(f"  Dry Run: {args.dry_run}", flush=True)
    print(f"  Started: {datetime.now().isoformat()}", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    # 1. Get GlobalHouse product for this SKU
    print(f"[1/4] Looking up GlobalHouse product for TWD SKU {args.sku}...", flush=True)
    gbh_product = get_gbh_product_for_sku(args.sku)
    
    if not gbh_product:
        print(f"❌ ERROR: No verified GlobalHouse match found for TWD SKU {args.sku}", flush=True)
        print("\nPossible reasons:", flush=True)
        print("  • SKU doesn't exist in products table", flush=True)
        print("  • No verified product match exists", flush=True)
        print("  • GlobalHouse product has no link", flush=True)
        sys.exit(1)
    
    print(f"✓ Found GlobalHouse match:", flush=True)
    print(f"  TWD: [{gbh_product['twd_sku']}] {gbh_product['twd_name']}", flush=True)
    print(f"       Current Price: ฿{gbh_product['twd_current_price']:,.2f}" if gbh_product['twd_current_price'] else "       Current Price: N/A", flush=True)
    print(f"  GBH: [{gbh_product['gbh_sku']}] {gbh_product['gbh_name']}", flush=True)
    print(f"       Current Price: ฿{gbh_product['gbh_current_price']:,.2f}" if gbh_product['gbh_current_price'] else "       Current Price: N/A", flush=True)
    print(f"  URL: {gbh_product['gbh_link']}", flush=True)
    print(flush=True)
    
    # 2. Get monitored locations
    print("[2/4] Loading monitored locations...", flush=True)
    locations = get_monitored_locations()
    
    if not locations:
        print("❌ ERROR: No monitored locations found", flush=True)
        print("\nTo add monitored locations:", flush=True)
        print("  INSERT INTO location_monitored_locations (location_id)", flush=True)
        print("  SELECT location_id FROM locations WHERE retailer_id = 'gbh';", flush=True)
        sys.exit(1)
    
    print(f"✓ Found {len(locations)} monitored location(s):", flush=True)
    for loc in locations:
        print(f"  • [{loc['branch_code']}] {loc['name_th']} ({loc['name_en']})", flush=True)
    print(flush=True)
    
    # 3. Initialize updater
    print("[3/4] Initializing location price updater...", flush=True)
    updater = LocationPriceUpdater(
        batch_size=1,
        delay_between_products=0,  # No delay for single product test
        dry_run=args.dry_run,
        parallel_workers=1,
        scrape_timeout=args.timeout
    )
    print(f"✓ Updater initialized (dry_run={args.dry_run}, timeout={args.timeout}s)", flush=True)
    print(flush=True)
    
    # 4. Scrape and update prices for each location
    print(f"[4/4] Scraping prices across {len(locations)} location(s)...", flush=True)
    print("-" * 80, flush=True)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, location in enumerate(locations, 1):
        print(f"\n[{i}/{len(locations)}] {location['name_th']} ({location['branch_code']})", flush=True, end=' ')
        
        # Scrape with location
        scraped_data = updater.scrape_product_with_location(
            url=gbh_product['gbh_link'],
            location_name_th=location['name_th']
        )
        
        if not scraped_data:
            print(f"❌ Error", flush=True)
        elif not scraped_data.get('current_price'):
            print(f"⚠ No price", flush=True)
        
        if scraped_data and 'current_price' in scraped_data and scraped_data['current_price']:
            price = float(scraped_data['current_price'])
            print(f"✓ ฿{price:,.2f}", flush=True)
            
            # Update database
            if not args.dry_run:
                updater.update_location_price(
                    product_id=gbh_product['gbh_product_id'],
                    location_id=location['location_id'],
                    price=price
                )
            else:
                print(f"  (dry run - not saved)", flush=True)
            
            results.append({
                'location': location['name_th'],
                'branch_code': location['branch_code'],
                'price': price,
                'status': 'success'
            })
            success_count += 1
        else:
            results.append({
                'location': location['name_th'],
                'branch_code': location['branch_code'],
                'price': None,
                'status': 'failed'
            })
            fail_count += 1
    
    # Summary
    print(flush=True)
    print("=" * 80, flush=True)
    print("  SUMMARY", flush=True)
    print("=" * 80, flush=True)
    print(f"Total Locations: {len(locations)}", flush=True)
    print(f"Successful: {success_count}", flush=True)
    print(f"Failed: {fail_count}", flush=True)
    print(flush=True)
    
    # Price comparison table
    if success_count > 0:
        print("Price Comparison:", flush=True)
        print("-" * 80, flush=True)
        print(f"{'Location':<25} {'Branch Code':<15} {'Price':>15}", flush=True)
        print("-" * 80, flush=True)
        
        prices = []
        for result in results:
            if result['status'] == 'success':
                print(f"{result['location']:<25} {result['branch_code']:<15} ฿{result['price']:>13,.2f}", flush=True)
                prices.append(result['price'])
            else:
                print(f"{result['location']:<25} {result['branch_code']:<15} {'N/A':>15}", flush=True)
        
        print("-" * 80, flush=True)
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            print(f"{'Average:':<25} {'':<15} ฿{avg_price:>13,.2f}", flush=True)
            print(f"{'Lowest:':<25} {'':<15} ฿{min_price:>13,.2f}", flush=True)
            print(f"{'Highest:':<25} {'':<15} ฿{max_price:>13,.2f}", flush=True)
            
            # Compare with TWD price
            if gbh_product['twd_current_price']:
                twd_price = float(gbh_product['twd_current_price'])
                print(f"{'Thai Watsadu:':<25} {'':<15} ฿{twd_price:>13,.2f}", flush=True)
                
                # Find cheapest location vs TWD
                if min_price < twd_price:
                    savings = twd_price - min_price
                    savings_pct = (savings / twd_price) * 100
                    print(f"\n✓ Best GlobalHouse location is ฿{savings:,.2f} cheaper than TWD ({savings_pct:.1f}% savings)", flush=True)
                elif min_price > twd_price:
                    diff = min_price - twd_price
                    diff_pct = (diff / twd_price) * 100
                    print(f"\nℹ Thai Watsadu is ฿{diff:,.2f} cheaper than best GBH location ({diff_pct:.1f}% cheaper)", flush=True)
                else:
                    print(f"\nℹ Same price at best GlobalHouse location", flush=True)
    
    print(flush=True)
    print("=" * 80, flush=True)
    print(f"Completed: {datetime.now().isoformat()}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

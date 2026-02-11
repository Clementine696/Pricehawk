"""
Location-based Price Updater Service (GlobalHouse Only)

Service to scrape location-specific prices for monitored products across monitored locations.
Designed specifically for GlobalHouse which supports location selection.

Features:
- Scrapes prices for monitored watchlist groups across monitored locations
- Only processes verified GlobalHouse product matches
- Updates product_location_prices and location_price_history
- Parallel processing support
- Memory-efficient with cleanup

Usage:
    python location_price_updater.py                    # Update all monitored products/locations
    python location_price_updater.py --dry-run          # Test without updating DB
    python location_price_updater.py --parallel 3       # 3 parallel workers
    python location_price_updater.py --limit-groups 1   # Test with 1 group only
    python location_price_updater.py --limit-locations 2 # Test with 2 locations only

Environment Variables:
    LOC_UPDATE_BATCH_SIZE=10       # Products per batch
    LOC_UPDATE_DELAY=2.0           # Delay between products (seconds)
    LOC_UPDATE_PARALLEL=1          # Parallel workers (1=sequential)
    LOC_UPDATE_TIMEOUT=120         # Timeout per product (seconds)
"""

import os
import sys
import json
import subprocess
import logging
import gc
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from threading import Lock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

from database import get_db


def _env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.environ.get(key, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    elif value in ('false', '0', 'no', 'off'):
        return False
    return default


# Setup logging
WRITE_LOG_FILE = _env_bool('UPDATER_WRITE_LOG', True)
log_handlers = [logging.StreamHandler()]
if WRITE_LOG_FILE:
    log_handlers.append(logging.FileHandler(f'location_price_update_{datetime.now().strftime("%Y%m%d")}.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


@dataclass
class LocationUpdateStats:
    """Statistics for location price update run (thread-safe)"""
    total_combinations: int = 0  # Total (product × location) combinations
    updated: int = 0
    failed: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def increment(self, field_name: str, value: int = 1):
        """Thread-safe increment of a stat field"""
        with self._lock:
            current = getattr(self, field_name)
            setattr(self, field_name, current + value)

    def to_dict(self) -> Dict:
        return {
            'total_combinations': self.total_combinations,
            'updated': self.updated,
            'failed': self.failed,
        }


def cleanup_orphan_browsers():
    """Kill scraper-related browser processes to prevent memory accumulation."""
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
        logger.warning("psutil not available - skipping browser cleanup")
        return 0

    killed_count = 0

    if PSUTIL_AVAILABLE:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pinfo = proc.info
                    name = pinfo['name'].lower() if pinfo['name'] else ''
                    cmdline = pinfo['cmdline'] if pinfo['cmdline'] else []
                    cmdline_str = ' '.join(cmdline).lower()

                    # Only kill if it's a Chrome/Chromium process
                    if not any(browser in name for browser in ['chrome', 'chromium']):
                        continue

                    # Check if it's a scraper browser
                    is_scraper_browser = False

                    if 'playwright' in cmdline_str or 'crawl4ai' in cmdline_str:
                        is_scraper_browser = True
                    elif any(flag in cmdline for flag in ['--disable-dev-shm-usage', '--no-sandbox']) and '--headless' in cmdline:
                        has_user_profile = any(
                            '--profile-directory' in str(arg) or
                            ('--user-data-dir' in str(arg) and os.path.expanduser('~') in str(arg))
                            for arg in cmdline
                        )
                        if not has_user_profile:
                            is_scraper_browser = True

                    if is_scraper_browser:
                        try:
                            proc_obj = psutil.Process(pinfo['pid'])
                            children = proc_obj.children(recursive=True)
                            for child in children:
                                try:
                                    child.kill()
                                    killed_count += 1
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                            proc_obj.kill()
                            killed_count += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    pass

            if killed_count > 0:
                logger.info(f"  Killed {killed_count} scraper browser processes")
        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")

    return killed_count


def get_memory_usage() -> tuple:
    """Get current memory usage in MB. Returns (used_mb, percent, available_mb)"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        used_mb = mem.used / (1024 * 1024)
        percent = mem.percent
        available_mb = mem.available / (1024 * 1024)
        return (used_mb, percent, available_mb)
    except ImportError:
        return (0, 0, 0)


class LocationPriceUpdater:
    """
    Service to update location-specific prices for GlobalHouse products.

    Processes: monitored_groups × monitored_locations
    """

    # Scraper script path
    SCRAPER_SCRIPT = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "scraper-url", "adws", "adw_ecommerce_product_scraper.py"
    )

    def __init__(
        self,
        batch_size: int = 10,
        delay_between_products: float = 2.0,
        max_retries: int = 2,
        dry_run: bool = False,
        parallel_workers: int = 1,
        scrape_timeout: int = 120
    ):
        """
        Initialize location price updater.

        Args:
            batch_size: Products to process per batch
            delay_between_products: Seconds to wait between products
            max_retries: Max retry attempts for failed scrapes
            dry_run: If True, don't update database
            parallel_workers: Number of parallel workers (1 = sequential)
            scrape_timeout: Timeout in seconds for each scrape
        """
        self.batch_size = batch_size
        self.delay_between_products = delay_between_products
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.parallel_workers = max(1, min(parallel_workers, 10))
        self.scrape_timeout = scrape_timeout
        self.stats = LocationUpdateStats()
        self.results_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "results", "location_updates"
        )
        os.makedirs(self.results_dir, exist_ok=True)

    def get_monitored_groups(self) -> List[Dict]:
        """Get all monitored S-dept groups."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT
                        wsg.group_id,
                        wsg.name,
                        wsg.display_name
                    FROM location_monitored_groups lmg
                    JOIN watchlist_sku_groups wsg ON lmg.group_id = wsg.group_id
                    ORDER BY wsg.group_id
                """)
                return [dict(row) for row in cur.fetchall()]

    def get_monitored_locations(self) -> List[Dict]:
        """Get all monitored locations."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        l.location_id,
                        l.retailer_id,
                        l.name_th,
                        l.name_en,
                        l.url_param,
                        l.branch_code
                    FROM location_monitored_locations lml
                    JOIN locations l ON lml.location_id = l.location_id
                    WHERE l.is_active = TRUE
                    ORDER BY l.location_id
                """)
                return [dict(row) for row in cur.fetchall()]

    def get_gbh_products_for_group(self, group_id: int) -> List[Dict]:
        """
        Get GlobalHouse products that are verified matches for Thai Watsadu SKUs in the group.

        Args:
            group_id: S-dept group ID

        Returns:
            List of GlobalHouse products with matched TWD info
        """
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT
                        p_gbh.product_id as gbh_product_id,
                        p_gbh.sku as gbh_sku,
                        p_gbh.name as gbh_name,
                        p_gbh.link as gbh_link,
                        p_twd.sku as twd_sku,
                        p_twd.name as twd_name
                    FROM watchlist_sku_group_products wsgp
                    JOIN products p_twd ON wsgp.sku = p_twd.sku AND p_twd.retailer_id = 'twd'
                    JOIN product_matches pm ON pm.base_product_id = p_twd.product_id
                        AND pm.verified_by_user = TRUE
                        AND pm.is_same = TRUE
                    JOIN products p_gbh ON pm.candidate_product_id = p_gbh.product_id
                        AND p_gbh.retailer_id = 'gbh'
                    WHERE wsgp.group_id = %s
                        AND p_gbh.link IS NOT NULL
                        AND p_gbh.link != ''
                    ORDER BY p_gbh.product_id
                """, (group_id,))
                return [dict(row) for row in cur.fetchall()]

    def scrape_product_with_location(
        self,
        url: str,
        location_name_th: str
    ) -> Optional[Dict]:
        """
        Scrape a GlobalHouse product with location selection.

        Args:
            url: Product URL
            location_name_th: Location name in Thai (e.g., "นครปฐม", "ขอนแก่น")

        Returns:
            Scraped product data with price, or None if failed
        """
        import uuid
        import time

        output_file = os.path.join(self.results_dir, f"scrape_{uuid.uuid4().hex}.json")

        # Use --gbh-location parameter to trigger location selection
        cmd = [
            "python", self.SCRAPER_SCRIPT,
            "--url", url,
            "--gbh-location", location_name_th,
            "--output-file", output_file
        ]

        process = None
        result_data = None

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # Limit threads to prevent exhaustion
            env["OPENBLAS_NUM_THREADS"] = "1"
            env["MKL_NUM_THREADS"] = "1"
            env["NUMEXPR_NUM_THREADS"] = "1"
            env["OMP_NUM_THREADS"] = "1"

            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'encoding': 'utf-8',
                'errors': 'replace',
                'env': env,
                'cwd': os.path.dirname(self.SCRAPER_SCRIPT)
            }

            if hasattr(os, 'setsid'):
                popen_kwargs['start_new_session'] = True

            process = subprocess.Popen(cmd, **popen_kwargs)

            try:
                stdout, stderr = process.communicate(timeout=self.scrape_timeout)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                logger.error(f"Timeout scraping {url} with location {location_url_param}")
                return None

            if returncode != 0:
                logger.warning(f"Scraper failed: {stderr[:200] if stderr else 'No error'}")
                return None

            # Look for GlobalHouse output file
            output_dir = os.path.dirname(output_file)
            gbh_files = ['global_house.json', 'globalhouse.json']

            for filename in gbh_files:
                filepath = os.path.join(output_dir, filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if isinstance(data, list) and len(data) > 0:
                            result_data = data[0]
                            break
                        elif isinstance(data, dict):
                            result_data = data
                            break
                    except Exception as e:
                        logger.error(f"Error reading {filepath}: {e}")

            # Also check direct output file
            if not result_data and os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        result_data = data[0]
                    elif isinstance(data, dict):
                        result_data = data
                except Exception as e:
                    logger.error(f"Error reading output file: {e}")

            return result_data

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

        finally:
            # Cleanup process
            if process is not None:
                try:
                    if process.poll() is None:
                        try:
                            import psutil
                            parent = psutil.Process(process.pid)
                            children = parent.children(recursive=True)
                            for child in children:
                                try:
                                    child.kill()
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                            parent.kill()
                            process.wait(timeout=3)
                        except Exception:
                            process.kill()
                            try:
                                process.wait(timeout=2)
                            except Exception:
                                pass

                    if process.stdout:
                        process.stdout.close()
                    if process.stderr:
                        process.stderr.close()
                except Exception:
                    pass

            # Clean up temp files
            try:
                if os.path.exists(output_file):
                    os.remove(output_file)
                output_dir = os.path.dirname(output_file)
                for filename in ['global_house.json', 'globalhouse.json']:
                    filepath = os.path.join(output_dir, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
            except Exception:
                pass

            # Aggressive cleanup
            cleanup_orphan_browsers()
            gc.collect()

    def update_location_price(
        self,
        product_id: int,
        location_id: int,
        price: float
    ) -> bool:
        """
        Update product location price in database.

        Args:
            product_id: GlobalHouse product ID
            location_id: Location ID
            price: Scraped price

        Returns:
            True if updated successfully
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update product {product_id} at location {location_id}: ฿{price}")
            return True

        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    # Upsert product_location_prices
                    cur.execute("""
                        INSERT INTO product_location_prices (product_id, location_id, price, last_updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (product_id, location_id)
                        DO UPDATE SET
                            price = EXCLUDED.price,
                            last_updated_at = EXCLUDED.last_updated_at
                    """, (product_id, location_id, price))

                    # Insert into history
                    cur.execute("""
                        INSERT INTO location_price_history (product_id, location_id, price, scraped_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (product_id, location_id, price))

                    conn.commit()

            self.stats.increment('updated')
            return True

        except Exception as e:
            logger.error(f"Database error updating location price: {e}")
            self.stats.increment('failed')
            return False

    def process_batch(
        self,
        products: List[Dict],
        locations: List[Dict]
    ) -> int:
        """
        Process a batch of products across all locations.

        Args:
            products: List of GlobalHouse products
            locations: List of locations

        Returns:
            Number of successfully updated combinations
        """
        import time

        updated = 0

        for i, product in enumerate(products):
            logger.info(f"  [{i+1}/{len(products)}] Processing {product['gbh_sku']} - {product['gbh_name'][:50]}...")

            # Scrape this product for each location
            for loc in locations:
                location_name = loc['name_th'] or loc['name_en']
                logger.info(f"    → Location: {location_name}")

                scraped = None
                for attempt in range(self.max_retries):
                    scraped = self.scrape_product_with_location(
                        product['gbh_link'],
                        loc['name_th']
                    )
                    if scraped:
                        break
                    logger.warning(f"    Retry {attempt + 1}/{self.max_retries}")
                    time.sleep(self.delay_between_products)

                if scraped and scraped.get('current_price'):
                    price = float(scraped['current_price'])
                    if self.update_location_price(
                        product['gbh_product_id'],
                        loc['location_id'],
                        price
                    ):
                        updated += 1
                        logger.info(f"    Updated: ฿{price}")
                    else:
                        logger.error(f"    Failed to update database")
                else:
                    self.stats.increment('failed')
                    logger.error(f"    Failed to scrape price")

                # Rate limiting between locations
                time.sleep(self.delay_between_products)

        return updated

    def run(
        self,
        limit_groups: Optional[int] = None,
        limit_locations: Optional[int] = None
    ) -> LocationUpdateStats:
        """
        Run the location price update process.

        Args:
            limit_groups: Optional limit to N groups for testing
            limit_locations: Optional limit to N locations for testing

        Returns:
            Update statistics
        """
        start_time = datetime.now()
        used_mb, percent, available_mb = get_memory_usage()

        logger.info("=" * 60)
        logger.info(f"Location Price Update Started: {start_time}")
        logger.info(f"Configuration: batch_size={self.batch_size}, parallel_workers={self.parallel_workers}, dry_run={self.dry_run}")
        logger.info(f"Memory at start: {percent:.1f}% ({used_mb/1024:.2f}GB used)")
        logger.info("=" * 60)

        # Initial cleanup
        logger.info("Running initial browser cleanup...")
        cleanup_orphan_browsers()
        gc.collect()

        # Get monitored groups and locations
        groups = self.get_monitored_groups()
        locations = self.get_monitored_locations()

        if limit_groups:
            groups = groups[:limit_groups]
            logger.info(f"Limited to {len(groups)} groups (testing)")

        if limit_locations:
            locations = locations[:limit_locations]
            logger.info(f"Limited to {len(locations)} locations (testing)")

        if not groups:
            logger.warning("No monitored groups found. Configure in /price-by-location/settings")
            return self.stats

        if not locations:
            logger.warning("No monitored locations found. Configure in /price-by-location/settings")
            return self.stats

        logger.info(f"\nMonitored groups: {len(groups)}")
        for g in groups:
            logger.info(f"  - {g['display_name']} (ID: {g['group_id']})")

        logger.info(f"\nMonitored locations: {len(locations)}")
        for loc in locations:
            logger.info(f"  - {loc['name_th']} ({loc['branch_code']})")

        # Process each group
        for group in groups:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing Group: {group['display_name']}")
            logger.info(f"{'='*60}")

            # Get GlobalHouse products for this group
            products = self.get_gbh_products_for_group(group['group_id'])

            if not products:
                logger.info(f"No GlobalHouse products found for group {group['display_name']}")
                continue

            logger.info(f"Found {len(products)} GlobalHouse products in this group")

            # Calculate total combinations
            total_combos = len(products) * len(locations)
            self.stats.total_combinations += total_combos
            logger.info(f"Total combinations to scrape: {len(products)} products × {len(locations)} locations = {total_combos}")

            # Process in batches
            for batch_start in range(0, len(products), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(products))
                batch = products[batch_start:batch_end]

                logger.info(f"\nBatch {batch_start//self.batch_size + 1}: products {batch_start + 1}-{batch_end}")
                self.process_batch(batch, locations)

                # Cleanup between batches
                if batch_end < len(products):
                    logger.info(f"Waiting before next batch...")
                    cleanup_orphan_browsers()
                    gc.collect()
                    import time
                    time.sleep(5)

        # Final cleanup
        logger.info("\nRunning final cleanup...")
        cleanup_orphan_browsers()
        gc.collect()

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        used_mb, percent, available_mb = get_memory_usage()

        logger.info("\n" + "=" * 60)
        logger.info("LOCATION PRICE UPDATE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Total Combinations: {self.stats.total_combinations}")
        logger.info(f"Updated: {self.stats.updated}")
        logger.info(f"Failed: {self.stats.failed}")
        logger.info(f"Memory at end: {percent:.1f}% ({used_mb/1024:.2f}GB used)")
        logger.info("=" * 60)

        return self.stats


def main():
    """CLI entry point"""
    import argparse

    # Get defaults from environment variables
    env_batch_size = int(os.environ.get('LOC_UPDATE_BATCH_SIZE', 10))
    env_delay = float(os.environ.get('LOC_UPDATE_DELAY', 2.0))
    env_parallel = int(os.environ.get('LOC_UPDATE_PARALLEL', 1))
    env_timeout = int(os.environ.get('LOC_UPDATE_TIMEOUT', 120))

    parser = argparse.ArgumentParser(description='Update location-based prices for GlobalHouse')
    parser.add_argument('--batch-size', '-b', type=int, default=env_batch_size,
                       help=f'Batch size (default: {env_batch_size})')
    parser.add_argument('--delay', '-d', type=float, default=env_delay,
                       help=f'Delay between products in seconds (default: {env_delay})')
    parser.add_argument('--parallel', '-p', type=int, default=env_parallel,
                       help=f'Parallel workers (default: {env_parallel})')
    parser.add_argument('--timeout', '-t', type=int, default=env_timeout,
                       help=f'Timeout per product in seconds (default: {env_timeout})')
    parser.add_argument('--dry-run', action='store_true', help='Test without updating database')
    parser.add_argument('--limit-groups', type=int, help='Limit to N groups for testing')
    parser.add_argument('--limit-locations', type=int, help='Limit to N locations for testing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    updater = LocationPriceUpdater(
        batch_size=args.batch_size,
        delay_between_products=args.delay,
        parallel_workers=args.parallel,
        dry_run=args.dry_run,
        scrape_timeout=args.timeout
    )

    stats = updater.run(
        limit_groups=args.limit_groups,
        limit_locations=args.limit_locations
    )

    # Exit with error code if too many failures
    failure_rate = stats.failed / stats.total_combinations if stats.total_combinations > 0 else 0
    if failure_rate > 0.5:
        logger.error(f"High failure rate: {failure_rate:.1%}")
        sys.exit(1)


if __name__ == "__main__":
    main()

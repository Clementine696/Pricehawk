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
- LIMIT/OFFSET support for incremental processing

Usage:
    python location_price_updater.py                    # Update all monitored products/locations
    python location_price_updater.py --dry-run          # Test without updating DB
    python location_price_updater.py --parallel 3       # 3 parallel workers
    python location_price_updater.py --limit 100        # Process only 100 combinations
    python location_price_updater.py --offset 100       # Skip first 100 combinations
    python location_price_updater.py --limit-groups 1   # Test with 1 group only
    python location_price_updater.py --limit-locations 2 # Test with 2 locations only

Environment Variables:
    GBH_UPDATE_BATCH_SIZE=20       # Products per batch
    GBH_UPDATE_DELAY=2.0           # Delay between products (seconds)
    GBH_UPDATE_PARALLEL=1          # Parallel workers (1=sequential)
    GBH_UPDATE_TIMEOUT=120         # Timeout per product (seconds)
    GBH_UPDATE_LIMIT=100           # Limit combinations per run (for incremental updates)
    GBH_UPDATE_OFFSET=0            # Skip N combinations (continue from previous run)
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
    log_handlers.append(logging.FileHandler(f'location_price_update_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'))

# Configure stream handler with UTF-8 encoding for Windows
if log_handlers[0].__class__.__name__ == 'StreamHandler':
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

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
                        wsg.name
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
                        l.branch_code
                    FROM location_monitored_locations lml
                    JOIN locations l ON lml.location_id = l.location_id
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
                logger.error(f"Timeout scraping {url} with location {location_name_th}")
                return None

            # Log errors only on failure
            if returncode != 0:
                if stderr:
                    err_lines = [line for line in stderr.split('\n') if 'ERROR' in line or 'FAILED' in line]
                    if err_lines:
                        print(f"⚠ Errors for {location_name_th}:", flush=True)
                        for line in err_lines[-3:]:
                            print(f"  {line}", flush=True)
                logger.warning(f"Scraper failed for {location_name_th}")
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
                            # If price is missing, log stderr for debugging
                            if not result_data.get('current_price'):
                                if stderr and 'STEP' in stderr:
                                    logger.warning(f"No price for {location_name_th}. Scraper logs:\n{stderr[-2000:]}")
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

    def mark_combination_failed(
        self,
        product_id: int,
        location_id: int
    ) -> bool:
        """
        Mark a combination as failed by updating timestamp without price.
        This moves it to the back of the queue (won't retry until next full cycle).

        Args:
            product_id: GlobalHouse product ID
            location_id: Location ID

        Returns:
            True if marked successfully
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would mark combination as failed: product {product_id} at location {location_id}")
            return True

        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    # Upsert with NULL price but update timestamp
                    # This prevents retry loop while keeping the combination tracked
                    cur.execute("""
                        INSERT INTO product_location_prices (product_id, location_id, price, last_updated_at)
                        VALUES (%s, %s, NULL, NOW())
                        ON CONFLICT (product_id, location_id)
                        DO UPDATE SET
                            last_updated_at = NOW()
                            -- Keep existing price if any, just update timestamp
                    """, (product_id, location_id))

                    conn.commit()

            return True

        except Exception as e:
            logger.error(f"Database error marking combination as failed: {e}")
            return False

    def get_all_combinations(
        self,
        limit_groups: Optional[int] = None,
        limit_locations: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all product×location combinations to process.
        
        Args:
            limit_groups: Optional limit to N groups for testing
            limit_locations: Optional limit to N locations for testing
            
        Returns:
            List of dicts with: {
                'group_id', 'group_name', 
                'gbh_product_id', 'gbh_sku', 'gbh_name', 'gbh_link',
                'location_id', 'location_name', 'branch_code',
                'last_updated_at'  # For sorting by least recently updated
            }
        """
        # Get monitored groups and locations
        groups = self.get_monitored_groups()
        locations = self.get_monitored_locations()

        if limit_groups:
            groups = groups[:limit_groups]
        if limit_locations:
            locations = locations[:limit_locations]

        if not groups or not locations:
            return []

        # Collect all product IDs from all groups
        all_product_ids = []
        product_info = {}  # product_id -> {group_id, group_name, sku, name, link}
        
        for group in groups:
            products = self.get_gbh_products_for_group(group['group_id'])
            for product in products:
                pid = product['gbh_product_id']
                all_product_ids.append(pid)
                product_info[pid] = {
                    'group_id': group['group_id'],
                    'group_name': group['name'],
                    'gbh_sku': product['gbh_sku'],
                    'gbh_name': product['gbh_name'],
                    'gbh_link': product['gbh_link']
                }

        if not all_product_ids:
            return []

        # Fetch all last_updated_at timestamps in ONE batch query
        location_ids = [loc['location_id'] for loc in locations]
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT product_id, location_id, last_updated_at
                    FROM product_location_prices
                    WHERE product_id = ANY(%s) AND location_id = ANY(%s)
                """, (all_product_ids, location_ids))
                timestamp_rows = cur.fetchall()
        
        # Build lookup: (product_id, location_id) -> last_updated_at
        timestamp_lookup = {
            (row['product_id'], row['location_id']): row['last_updated_at']
            for row in timestamp_rows
        }

        # Build all combinations
        combinations = []
        for pid, pinfo in product_info.items():
            for location in locations:
                loc_id = location['location_id']
                last_updated = timestamp_lookup.get((pid, loc_id), None)
                
                combinations.append({
                    'group_id': pinfo['group_id'],
                    'group_name': pinfo['group_name'],
                    'gbh_product_id': pid,
                    'gbh_sku': pinfo['gbh_sku'],
                    'gbh_name': pinfo['gbh_name'],
                    'gbh_link': pinfo['gbh_link'],
                    'location_id': loc_id,
                    'location_name': location['name_th'] or location['name_en'],
                    'branch_code': location['branch_code'],
                    'last_updated_at': last_updated
                })

        # Sort by least recently updated first (NULL = never updated = highest priority)
        combinations.sort(key=lambda x: x['last_updated_at'] or datetime.min)

        return combinations

    def process_combinations(
        self,
        combinations: List[Dict]
    ) -> int:
        """
        Process a list of product×location combinations.
        
        Args:
            combinations: List of combination dicts
            
        Returns:
            Number of successfully updated combinations
        """
        import time

        updated = 0

        for i, combo in enumerate(combinations):
            logger.info(f"[{i+1}/{len(combinations)}] {combo['gbh_sku']} @ {combo['location_name']} ({combo['branch_code']})")

            scraped = None
            for attempt in range(self.max_retries):
                scraped = self.scrape_product_with_location(
                    combo['gbh_link'],
                    combo['location_name']
                )
                if scraped:
                    break
                if attempt < self.max_retries - 1:
                    logger.warning(f"  Retry {attempt + 1}/{self.max_retries}")
                    time.sleep(self.delay_between_products)

            if scraped and scraped.get('current_price'):
                try:
                    price = float(scraped['current_price'])
                    if self.update_location_price(
                        combo['gbh_product_id'],
                        combo['location_id'],
                        price
                    ):
                        updated += 1
                        logger.info(f"  ✓ ฿{price}")
                    else:
                        logger.error(f"  ✗ Failed to update database")
                except (ValueError, TypeError) as e:
                    self.stats.increment('failed')
                    logger.error(f"  ✗ Invalid price: {e}")
                    # Mark as failed to move to back of queue
                    self.mark_combination_failed(combo['gbh_product_id'], combo['location_id'])
            else:
                # Failed to scrape after all retries
                self.stats.increment('failed')
                logger.error(f"  ✗ Failed to scrape after {self.max_retries} attempts")
                # Mark as failed to move to back of queue (prevents retry loop)
                self.mark_combination_failed(combo['gbh_product_id'], combo['location_id'])

            # Rate limiting
            time.sleep(self.delay_between_products)

            # Periodic cleanup every 10 combinations
            if (i + 1) % 10 == 0:
                cleanup_orphan_browsers()
                gc.collect()

        return updated

    def run(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        limit_groups: Optional[int] = None,
        limit_locations: Optional[int] = None
    ) -> LocationUpdateStats:
        """
        Run the location price update process.

        Args:
            limit: Limit to N combinations (for incremental updates)
            offset: Skip first N combinations (continue from previous run)
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
        logger.info(f"Limit: {limit or 'ALL'}, Offset: {offset}")
        logger.info(f"Memory at start: {percent:.1f}% ({used_mb/1024:.2f}GB used)")
        logger.info("=" * 60)

        # Initial cleanup
        logger.info("Running initial browser cleanup...")
        cleanup_orphan_browsers()
        gc.collect()

        # Get all combinations (sorted by least recently updated)
        logger.info("\nCollecting all product×location combinations...")
        all_combinations = self.get_all_combinations(limit_groups, limit_locations)

        if not all_combinations:
            logger.warning("No combinations to process. Check monitored groups/locations.")
            return self.stats

        total_available = len(all_combinations)
        logger.info(f"Total combinations available: {total_available}")

        # Apply offset
        if offset > 0:
            if offset >= total_available:
                logger.warning(f"Offset {offset} >= total combinations {total_available}. Nothing to process.")
                return self.stats
            all_combinations = all_combinations[offset:]
            logger.info(f"Skipped first {offset} combinations (offset)")

        # Apply limit
        if limit:
            all_combinations = all_combinations[:limit]
            logger.info(f"Limited to {len(all_combinations)} combinations")

        self.stats.total_combinations = len(all_combinations)

        # Show summary
        logger.info(f"\nProcessing range: combinations {offset + 1} to {offset + len(all_combinations)} of {total_available}")
        logger.info(f"Will process: {self.stats.total_combinations} combinations")

        # Group by product for display
        unique_products = len(set(c['gbh_product_id'] for c in all_combinations))
        unique_locations = len(set(c['location_id'] for c in all_combinations))
        logger.info(f"  - {unique_products} unique products")
        logger.info(f"  - {unique_locations} unique locations")

        # Process all combinations
        logger.info(f"\n{'='*60}")
        logger.info("Starting Price Scraping")
        logger.info(f"{'='*60}")

        updated = self.process_combinations(all_combinations)

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
        logger.info(f"Processed: {self.stats.total_combinations} combinations")
        logger.info(f"Updated: {self.stats.updated}")
        logger.info(f"Failed: {self.stats.failed}")
        if self.stats.total_combinations > 0:
            success_rate = (self.stats.updated / self.stats.total_combinations) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Memory at end: {percent:.1f}% ({used_mb/1024:.2f}GB used)")
        logger.info("=" * 60)

        # Show next offset for continuation
        next_offset = offset + self.stats.total_combinations
        if next_offset < total_available:
            remaining = total_available - next_offset
            logger.info(f"\n💡 To continue: --offset {next_offset} (remaining: {remaining} combinations)")

        return self.stats


def main():
    """CLI entry point"""
    import argparse

    # Get defaults from environment variables (updated to GBH_* prefix)
    env_batch_size = int(os.environ.get('GBH_UPDATE_BATCH_SIZE', 20))
    env_delay = float(os.environ.get('GBH_UPDATE_DELAY', 2.0))
    env_parallel = int(os.environ.get('GBH_UPDATE_PARALLEL', 1))
    env_timeout = int(os.environ.get('GBH_UPDATE_TIMEOUT', 120))
    env_limit = int(os.environ.get('GBH_UPDATE_LIMIT', 0)) if os.environ.get('GBH_UPDATE_LIMIT') else None
    env_offset = int(os.environ.get('GBH_UPDATE_OFFSET', 0))

    parser = argparse.ArgumentParser(description='Update location-based prices for GlobalHouse')
    parser.add_argument('--batch-size', '-b', type=int, default=env_batch_size,
                       help=f'Batch size (default: {env_batch_size})')
    parser.add_argument('--delay', '-d', type=float, default=env_delay,
                       help=f'Delay between products in seconds (default: {env_delay})')
    parser.add_argument('--parallel', '-p', type=int, default=env_parallel,
                       help=f'Parallel workers (default: {env_parallel})')
    parser.add_argument('--timeout', '-t', type=int, default=env_timeout,
                       help=f'Timeout per product in seconds (default: {env_timeout})')
    parser.add_argument('--limit', '-l', type=int, default=env_limit,
                       help=f'Limit combinations to process (default: {env_limit or "ALL"})')
    parser.add_argument('--offset', '-o', type=int, default=env_offset,
                       help=f'Skip first N combinations (default: {env_offset})')
    parser.add_argument('--dry-run', action='store_true', help='Test without updating database')
    parser.add_argument('--limit-groups', type=int, help='Limit to N groups for testing (overrides limit/offset)')
    parser.add_argument('--limit-locations', type=int, help='Limit to N locations for testing (overrides limit/offset)')
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
        limit=args.limit,
        offset=args.offset,
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

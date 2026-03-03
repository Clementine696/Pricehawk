#!/usr/bin/env python3
"""
GlobalHouse Price Update Cron Job

Updates GlobalHouse product prices using the เทพารักษ์ (THEPHARAK) branch.
Updates the main products table and price_history (not location-specific tables).

Railway Cron Setup:
1. Create new service in Railway
2. Set command: python update_globalhouse_prices.py
3. Set schedule: 0 3 * * * (daily at 3 AM UTC, which is 10 AM Thailand)

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- GBH_UPDATE_BATCH_SIZE: Products per batch (default: 20)
- GBH_UPDATE_DELAY: Delay between products in seconds (default: 2.0)
- GBH_UPDATE_PARALLEL: Number of parallel workers (default: 1)
- GBH_UPDATE_TIMEOUT: Timeout per product in seconds (default: 120)
- GBH_UPDATE_LIMIT: Optional limit on number of products to update
- GBH_UPDATE_OFFSET: Optional number of oldest products to skip (default: 0)
"""

import os
import sys
import json
import subprocess
import logging
import gc
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from threading import Lock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

from database import get_db


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'globalhouse_price_update_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)


# Fixed GlobalHouse branch for price updates
GBH_DEFAULT_BRANCH = {
    "branch_code": "GH-141",
    "branch_name_TH": "เทพารักษ์",
    "branch_name_EN": "THEPHARAK",
    "postal_code": 10540
}


@dataclass
class GBHUpdateStats:
    """Statistics for GlobalHouse price update run (thread-safe)"""
    total_products: int = 0
    updated: int = 0
    failed: int = 0
    unchanged: int = 0
    price_increased: int = 0
    price_decreased: int = 0
    new_lowest: int = 0
    new_highest: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def increment(self, field_name: str, value: int = 1):
        """Thread-safe increment of a stat field"""
        with self._lock:
            current = getattr(self, field_name)
            setattr(self, field_name, current + value)

    def to_dict(self) -> Dict:
        return {
            'total_products': self.total_products,
            'updated': self.updated,
            'failed': self.failed,
            'unchanged': self.unchanged,
            'price_increased': self.price_increased,
            'price_decreased': self.price_decreased,
            'new_lowest': self.new_lowest,
            'new_highest': self.new_highest,
        }


def cleanup_orphan_browsers():
    """Kill scraper-related browser processes to prevent memory accumulation."""
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
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


class GlobalHousePriceUpdater:
    """
    Service to update GlobalHouse product prices using a fixed branch location.
    Updates the main products table and price_history.
    """

    # Scraper script path
    SCRAPER_SCRIPT = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "scraper-url", "adws", "adw_ecommerce_product_scraper.py"
    )

    def __init__(
        self,
        batch_size: int = 20,
        delay_between_products: float = 2.0,
        max_retries: int = 2,
        dry_run: bool = False,
        scrape_timeout: int = 120
    ):
        """
        Initialize GlobalHouse price updater.

        Args:
            batch_size: Products to process per batch
            delay_between_products: Seconds to wait between products
            max_retries: Max retry attempts for failed scrapes
            dry_run: If True, don't update database
            scrape_timeout: Timeout in seconds for each scrape
        """
        self.batch_size = batch_size
        self.delay_between_products = delay_between_products
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.scrape_timeout = scrape_timeout
        self.stats = GBHUpdateStats()
        self.results_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "results", "gbh_price_updates"
        )
        os.makedirs(self.results_dir, exist_ok=True)
        self.branch_location = GBH_DEFAULT_BRANCH["branch_name_TH"]

    def get_globalhouse_products(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get GlobalHouse products from database, ordered by oldest update first.

        Only includes:
        1. Thai Watsadu matched products - GBH products that are verified matches
        2. Products with valid links

        Args:
            limit: Optional limit to fetch only N oldest products
            offset: Optional number of oldest products to skip

        Returns:
            List of GlobalHouse products (oldest updates first if limit is set)
        """
        with get_db() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT
                        p.product_id, p.retailer_id, p.sku, p.name,
                        p.link, p.current_price, p.original_price,
                        p.lowest_price, p.highest_price, p.last_updated_at,
                        p.scrape_fail_count
                    FROM products p
                    WHERE p.retailer_id = 'gbh'
                      AND p.link IS NOT NULL AND p.link != ''
                      AND (
                          -- Include verified matched products
                          EXISTS (
                              SELECT 1 FROM product_matches pm
                              WHERE pm.candidate_product_id = p.product_id
                              AND pm.verified_result = TRUE
                          )
                      )
                    ORDER BY p.last_updated_at ASC NULLS FIRST
                """
                params = []

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

                if offset:
                    query += " OFFSET %s"
                    params.append(offset)

                cur.execute(query, params)
                return [dict(p) for p in cur.fetchall()]

    def scrape_product_with_location(
        self,
        url: str,
        location_name_th: str
    ) -> Optional[Dict]:
        """
        Scrape a GlobalHouse product with location selection.

        Args:
            url: Product URL
            location_name_th: Location name in Thai (e.g., "เทพารักษ์")

        Returns:
            Scraped product data with price, or None if failed
        """
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

    def update_product_price(
        self,
        product: Dict,
        scraped_data: Dict
    ) -> bool:
        """
        Update product price in database.

        Args:
            product: Original product from database
            scraped_data: Fresh scraped data

        Returns:
            True if updated successfully
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update {product['sku']}: "
                       f"{product['current_price']} -> {scraped_data.get('current_price')}")
            return True

        new_price = scraped_data.get('current_price')
        new_original_price = scraped_data.get('original_price')

        if new_price is None:
            logger.warning(f"No price in scraped data for {product['sku']}")
            return False

        try:
            new_price = float(new_price)
        except (TypeError, ValueError):
            logger.warning(f"Invalid price format for {product['sku']}: {new_price}")
            return False

        old_price = float(product['current_price']) if product['current_price'] else None
        lowest_price = float(product['lowest_price']) if product['lowest_price'] else new_price
        highest_price = float(product['highest_price']) if product['highest_price'] else new_price

        # Track price changes
        if old_price:
            if new_price > old_price:
                self.stats.increment('price_increased')
            elif new_price < old_price:
                self.stats.increment('price_decreased')
            else:
                self.stats.increment('unchanged')

        # Update lowest/highest
        if new_price < lowest_price:
            lowest_price = new_price
            self.stats.increment('new_lowest')
        if new_price > highest_price:
            highest_price = new_price
            self.stats.increment('new_highest')

        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    # Update product (reset scrape_fail_count on success)
                    cur.execute("""
                        UPDATE products SET
                            current_price = %s,
                            original_price = COALESCE(%s, original_price),
                            lowest_price = %s,
                            highest_price = %s,
                            last_updated_at = NOW(),
                            scrape_fail_count = 0
                        WHERE product_id = %s
                    """, (
                        new_price,
                        new_original_price,
                        lowest_price,
                        highest_price,
                        product['product_id']
                    ))

                    # Insert price history
                    cur.execute("""
                        INSERT INTO price_history (product_id, price, scraped_at)
                        VALUES (%s, %s, NOW())
                    """, (product['product_id'], new_price))

                    conn.commit()

            self.stats.increment('updated')
            return True

        except Exception as e:
            logger.error(f"Database error updating {product['sku']}: {e}")
            self.stats.increment('failed')
            return False

    def record_scrape_failure(self, product: Dict):
        """
        Record a scrape failure for a product.
        Increments scrape_fail_count and updates last_updated_at.

        Args:
            product: Product that failed to scrape
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would record failure for {product['sku']}")
            return

        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE products SET
                            scrape_fail_count = scrape_fail_count + 1,
                            last_updated_at = NOW()
                        WHERE product_id = %s
                    """, (product['product_id'],))
                    conn.commit()

            current_fails = (product.get('scrape_fail_count') or 0) + 1
            logger.info(f"  Recorded failure {current_fails} for {product['sku']}")

        except Exception as e:
            logger.error(f"Failed to record scrape failure for {product['sku']}: {e}")

    def process_batch(self, products: List[Dict]) -> int:
        """
        Process a batch of products.

        Args:
            products: List of products to process

        Returns:
            Number of successfully updated products
        """
        updated = 0

        for i, product in enumerate(products):
            logger.info(f"  [{i+1}/{len(products)}] Processing {product['sku']} - {product['link'][:60]}...")

            scraped = None
            for attempt in range(self.max_retries):
                scraped = self.scrape_product_with_location(
                    product['link'],
                    self.branch_location
                )
                if scraped:
                    break
                if attempt < self.max_retries - 1:
                    logger.warning(f"  Retry {attempt + 1}/{self.max_retries}")
                    time.sleep(self.delay_between_products)

            if scraped:
                if self.update_product_price(product, scraped):
                    updated += 1
                    logger.info(f"  ✓ Updated: ฿{scraped.get('current_price')}")
                else:
                    logger.error(f"  ✗ Failed to update database")
                    self.record_scrape_failure(product)
            else:
                self.stats.increment('failed')
                logger.error(f"  ✗ Failed to scrape")
                self.record_scrape_failure(product)

            # Rate limiting
            if i < len(products) - 1:
                time.sleep(self.delay_between_products)

            # Memory cooldown: pause every 10 products
            if (i + 1) % 10 == 0:
                logger.info(f"  Memory cooldown... (every 10 products)")
                cleanup_orphan_browsers()
                gc.collect()
                time.sleep(2)

        return updated

    def run(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> GBHUpdateStats:
        """
        Run the GlobalHouse price update process.

        Args:
            limit: Optional limit to N products for testing
            offset: Optional offset to skip N oldest products

        Returns:
            Update statistics
        """
        start_time = datetime.now()
        used_mb, percent, available_mb = get_memory_usage()

        logger.info("=" * 70)
        logger.info("  PRICEHAWK GLOBALHOUSE PRICE UPDATE")
        logger.info(f"  Started: {start_time.isoformat()}")
        logger.info(f"  Branch: {self.branch_location} ({GBH_DEFAULT_BRANCH['branch_name_EN']})")
        logger.info("=" * 70)
        logger.info(f"Configuration:")
        logger.info(f"  Batch Size: {self.batch_size}")
        logger.info(f"  Delay: {self.delay_between_products}s")
        logger.info(f"  Product Limit: {limit or 'NONE (all products)'}")
        logger.info(f"  Offset: {offset}")
        logger.info(f"  Dry Run: {self.dry_run}")
        logger.info(f"Memory at start: {percent:.1f}% ({used_mb/1024:.2f}GB used)")

        # Initial cleanup
        logger.info("Running initial browser cleanup...")
        cleanup_orphan_browsers()
        gc.collect()

        # Get GlobalHouse products
        products = self.get_globalhouse_products(limit=limit, offset=offset)
        self.stats.total_products = len(products)

        if not products:
            logger.warning("No GlobalHouse products found.")
            return self.stats

        logger.info(f"\nFound {len(products)} GlobalHouse products to update")

        # Process in batches
        for batch_start in range(0, len(products), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(products))
            batch = products[batch_start:batch_end]

            logger.info(f"\n{'='*40}")
            logger.info(f"Batch {batch_start//self.batch_size + 1}: products {batch_start + 1}-{batch_end}")
            logger.info(f"{'='*40}")

            self.process_batch(batch)

            # Cleanup between batches
            if batch_end < len(products):
                logger.info(f"Waiting before next batch...")
                cleanup_orphan_browsers()
                gc.collect()
                time.sleep(5)

        # Final cleanup
        logger.info("\nRunning final cleanup...")
        cleanup_orphan_browsers()
        gc.collect()

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        used_mb, percent, available_mb = get_memory_usage()

        logger.info("\n" + "=" * 70)
        logger.info("GLOBALHOUSE PRICE UPDATE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration}")
        logger.info(f"Total Products: {self.stats.total_products}")
        logger.info(f"Updated: {self.stats.updated}")
        logger.info(f"Failed: {self.stats.failed}")
        logger.info(f"Unchanged: {self.stats.unchanged}")
        logger.info(f"Price Increased: {self.stats.price_increased}")
        logger.info(f"Price Decreased: {self.stats.price_decreased}")
        logger.info(f"New Lowest: {self.stats.new_lowest}")
        logger.info(f"New Highest: {self.stats.new_highest}")
        logger.info(f"Memory at end: {percent:.1f}% ({used_mb/1024:.2f}GB used)")

        # Calculate success rate
        if self.stats.total_products > 0:
            success_rate = (self.stats.updated / self.stats.total_products) * 100
            failure_rate = (self.stats.failed / self.stats.total_products) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
            logger.info(f"Failure Rate: {failure_rate:.1f}%")

        logger.info("=" * 70)

        return self.stats


def main():
    """Run GlobalHouse price update"""

    # Configuration from environment
    batch_size = int(os.environ.get('GBH_UPDATE_BATCH_SIZE', 20))
    delay = float(os.environ.get('GBH_UPDATE_DELAY', 2.0))
    timeout = int(os.environ.get('GBH_UPDATE_TIMEOUT', 120))
    limit_str = os.environ.get('GBH_UPDATE_LIMIT')
    limit = int(limit_str) if limit_str else None
    offset_str = os.environ.get('GBH_UPDATE_OFFSET')
    offset = int(offset_str) if offset_str else 0
    dry_run = os.environ.get('GBH_UPDATE_DRY_RUN', '').lower() in ('true', '1', 'yes')

    # Initialize and run
    updater = GlobalHousePriceUpdater(
        batch_size=batch_size,
        delay_between_products=delay,
        scrape_timeout=timeout,
        dry_run=dry_run
    )

    try:
        stats = updater.run(limit=limit, offset=offset)

        # Save run summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'branch': GBH_DEFAULT_BRANCH,
            'stats': stats.to_dict(),
            'config': {
                'batch_size': batch_size,
                'delay': delay,
                'timeout': timeout,
                'limit': limit,
                'offset': offset,
                'dry_run': dry_run
            }
        }

        summary_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'results', 'gbh_price_updates',
            f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"\nSummary saved to: {summary_file}")

        # Alert if high failure rate
        if stats.total_products > 0:
            failure_rate = (stats.failed / stats.total_products) * 100
            if failure_rate > 30:
                logger.warning(f"HIGH FAILURE RATE: {failure_rate:.1f}%")
                return 1

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

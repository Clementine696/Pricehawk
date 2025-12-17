"""
Price Updater Service

Service to update product prices by scraping retailer websites.
Designed to handle ~10,000 products efficiently.

Features:
- Limit mode: Update only N oldest products (ideal for hourly cron jobs)
- Failure tracking: Skip products after 3 consecutive failures (scrape_fail_count)
- Parallel processing across retailers
- Batch processing within each retailer
- Rate limiting to avoid being blocked
- Progress tracking and logging
- Price history recording

Failure Handling:
- On success: scrape_fail_count reset to 0
- On failure: scrape_fail_count incremented, last_updated_at updated
- Products with scrape_fail_count >= 3 are skipped
- To retry failed products: UPDATE products SET scrape_fail_count = 0 WHERE scrape_fail_count >= 3

Usage:
    python price_updater.py                    # Update all products
    python price_updater.py --limit 500        # Update 500 oldest products (for hourly cron)
    python price_updater.py --retailer twd     # Update specific retailer
    python price_updater.py --batch-size 100   # Custom batch size
    python price_updater.py --dry-run          # Test without updating DB
    python price_updater.py --parallel 3       # 3 parallel workers

Environment Variables:
    UPDATE_LIMIT=500          # Limit to N oldest products
    UPDATE_BATCH_SIZE=50      # Products per batch
    UPDATE_DELAY=1.0          # Delay between products (seconds)
    UPDATE_PARALLEL=1         # Parallel workers (1=sequential)
    UPDATE_TIMEOUT=120        # Timeout per product (seconds)
"""

import os
import sys
import json
import asyncio
import subprocess
import logging
import gc
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
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


# Setup logging - check if file logging is enabled
WRITE_LOG_FILE = _env_bool('UPDATER_WRITE_LOG', True)  # Default: write log file

log_handlers = [logging.StreamHandler()]
if WRITE_LOG_FILE:
    log_handlers.append(logging.FileHandler(f'price_update_{datetime.now().strftime("%Y%m%d")}.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


@dataclass
class UpdateStats:
    """Statistics for price update run (thread-safe)"""
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
    """
    Kill any orphaned chromium/chrome browser processes.
    This helps prevent memory accumulation on Railway.
    """
    import platform

    try:
        if platform.system() == 'Linux':
            # Kill chromium processes that might be orphaned
            subprocess.run(
                ['pkill', '-9', '-f', 'chromium'],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ['pkill', '-9', '-f', 'chrome'],
                capture_output=True,
                timeout=10
            )
        elif platform.system() == 'Windows':
            # Windows: use taskkill
            subprocess.run(
                ['taskkill', '/F', '/IM', 'chromium.exe'],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ['taskkill', '/F', '/IM', 'chrome.exe'],
                capture_output=True,
                timeout=10
            )
    except Exception:
        pass  # Ignore errors - this is best-effort cleanup


def cleanup_chrome_temp_dirs():
    """
    Clean up Chrome temp directories to prevent disk space accumulation.
    Chrome uses /tmp for cache when --disable-dev-shm-usage is set.
    Also cleans up Playwright temp directories that accumulate over time.
    """
    import platform
    import shutil
    import glob

    if platform.system() != 'Linux':
        return  # Only needed on Linux (Railway)

    try:
        # Direct cleanup of known directories
        tmp_dirs = [
            '/tmp/chrome-cache',
            # NOTE: Don't clean user-data-dir or crash-dumps-dir - we no longer use those flags
            # (Playwright requires launch_persistent_context() for --user-data-dir)
        ]

        for tmp_dir in tmp_dirs:
            if os.path.exists(tmp_dir):
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception:
                    pass

        # Clean up Playwright temp directories (pattern: playwright-*)
        # These accumulate with each browser launch and can cause issues
        playwright_temps = glob.glob('/tmp/playwright*')
        for temp_dir in playwright_temps:
            try:
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                else:
                    os.remove(temp_dir)
            except Exception:
                pass

        # Clean up any Chrome crash dumps
        chrome_temps = glob.glob('/tmp/.com.google.Chrome*') + glob.glob('/tmp/Crashpad*')
        for temp_dir in chrome_temps:
            try:
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                else:
                    os.remove(temp_dir)
            except Exception:
                pass

    except Exception:
        pass  # Ignore errors - this is best-effort cleanup


class PriceUpdater:
    """
    Service to update product prices from retailer websites.

    Processes products in batches, grouped by retailer to optimize
    browser reuse and respect rate limits.
    """

    # Scraper script path
    SCRAPER_SCRIPT = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scraper-url", "adws", "adw_ecommerce_product_scraper.py"
    )

    # Retailer file naming (scraper output files)
    RETAILER_FILES = {
        'twd': ['thai_watsadu.json', 'thaiwatsadu.json'],
        'hp': ['homepro.json', 'home_pro.json'],
        'dh': ['dohome.json', 'do_home.json'],
        'btv': ['boonthavorn.json'],
        'gbh': ['global_house.json', 'globalhouse.json'],
        'mgh': ['mega_home.json', 'megahome.json'],
    }

    def __init__(
        self,
        batch_size: int = 50,
        delay_between_batches: float = 2.0,
        delay_between_products: float = 1.0,
        max_retries: int = 2,
        dry_run: bool = False,
        parallel_workers: int = 1,
        scrape_timeout: int = 120
    ):
        """
        Initialize price updater.

        Args:
            batch_size: Products to process per batch
            delay_between_batches: Seconds to wait between batches
            delay_between_products: Seconds to wait between products (rate limiting)
            max_retries: Max retry attempts for failed scrapes
            dry_run: If True, don't update database
            parallel_workers: Number of parallel retailer workers (1 = sequential)
            scrape_timeout: Timeout in seconds for each product scrape
        """
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.delay_between_products = delay_between_products
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.parallel_workers = max(1, min(parallel_workers, 20))  # Clamp between 1-20
        self.scrape_timeout = scrape_timeout
        self.stats = UpdateStats()
        self.results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "results", "price_updates"
        )
        os.makedirs(self.results_dir, exist_ok=True)

    def get_products_by_retailer(self, retailer_id: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Get all products from database grouped by retailer.

        Args:
            retailer_id: Optional filter for specific retailer

        Returns:
            Dict mapping retailer_id to list of products
        """
        products_by_retailer = defaultdict(list)

        with get_db() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT
                        p.product_id, p.retailer_id, p.sku, p.name,
                        p.link, p.current_price, p.original_price,
                        p.lowest_price, p.highest_price, p.last_updated_at
                    FROM products p
                    WHERE p.link IS NOT NULL AND p.link != ''
                """
                params = []

                if retailer_id:
                    query += " AND p.retailer_id = %s"
                    params.append(retailer_id)

                query += " ORDER BY p.retailer_id, p.product_id"

                cur.execute(query, params)
                products = cur.fetchall()

                for product in products:
                    products_by_retailer[product['retailer_id']].append(dict(product))

        return dict(products_by_retailer)

    # Maximum consecutive failures before skipping a product
    MAX_SCRAPE_FAILURES = 3

    def get_all_products(self, retailer_id: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        Get products from database as a flat list, ordered by oldest update first.
        Skips products that have failed too many times (scrape_fail_count >= MAX_SCRAPE_FAILURES).

        Args:
            retailer_id: Optional filter for specific retailer
            limit: Optional limit to fetch only N oldest products (by last_updated_at)

        Returns:
            List of products (oldest updates first if limit is set)
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
                    WHERE p.link IS NOT NULL AND p.link != ''
                      AND (p.scrape_fail_count IS NULL OR p.scrape_fail_count < %s)
                """
                params = [self.MAX_SCRAPE_FAILURES]

                if retailer_id:
                    query += " AND p.retailer_id = %s"
                    params.append(retailer_id)

                # Order by oldest update first (NULL = never updated = highest priority)
                query += " ORDER BY p.last_updated_at ASC NULLS FIRST"

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

                cur.execute(query, params)
                return [dict(p) for p in cur.fetchall()]

    def process_worker_chunk(self, worker_id: int, products: List[Dict]) -> int:
        """
        Process a chunk of products assigned to a worker.

        Args:
            worker_id: Worker identifier (1-indexed)
            products: List of products to process

        Returns:
            Number of successfully updated products
        """
        import time

        logger.info(f"\n{'='*40}")
        logger.info(f"Worker {worker_id}: Processing {len(products)} products")
        logger.info(f"{'='*40}")

        total_updated = 0

        # Process in batches
        for batch_start in range(0, len(products), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(products))
            batch = products[batch_start:batch_end]

            logger.info(f"\n[Worker {worker_id}] Batch {batch_start//self.batch_size + 1}: "
                       f"products {batch_start + 1}-{batch_end}")

            total_updated += self.process_batch(batch)

            # Delay between batches
            if batch_end < len(products):
                logger.info(f"[Worker {worker_id}] Waiting {self.delay_between_batches}s before next batch...")
                time.sleep(self.delay_between_batches)

                # Periodic cleanup: kill any orphaned browser processes
                # This prevents memory accumulation over long runs
                batch_num = batch_start // self.batch_size + 1
                if batch_num % 3 == 0:  # Every 3 batches (was 5)
                    logger.info(f"[Worker {worker_id}] Running periodic browser + temp cleanup...")
                    cleanup_orphan_browsers()
                    cleanup_chrome_temp_dirs()  # Clean up /tmp/chrome-* directories
                    gc.collect()
                    time.sleep(5)  # Extra pause after major cleanup

        logger.info(f"\n[Worker {worker_id}] Completed: {total_updated}/{len(products)} updated")
        return total_updated

    def scrape_product(self, url: str) -> Optional[Dict]:
        """
        Scrape a single product URL using the existing scraper.

        Args:
            url: Product URL to scrape

        Returns:
            Scraped product data or None if failed
        """
        import uuid
        import gc

        output_file = os.path.join(self.results_dir, f"scrape_{uuid.uuid4().hex}.json")

        cmd = [
            "python", self.SCRAPER_SCRIPT,
            "--url", url,
            "--output-file", output_file
        ]

        process = None
        result_data = None

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # CRITICAL: Limit OpenBLAS/numpy threads to prevent thread exhaustion
            # Without these, each subprocess tries to create 48 threads, causing
            # "pthread_create failed" errors when running multiple workers
            env["OPENBLAS_NUM_THREADS"] = "1"
            env["MKL_NUM_THREADS"] = "1"
            env["NUMEXPR_NUM_THREADS"] = "1"
            env["OMP_NUM_THREADS"] = "1"
            env["VECLIB_MAXIMUM_THREADS"] = "1"

            # Use Popen for better control over process cleanup
            # On Linux, start in new process group so we can kill all children
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'encoding': 'utf-8',
                'errors': 'replace',
                'env': env,
                'cwd': os.path.dirname(self.SCRAPER_SCRIPT)
            }

            # Linux/Unix: start new process group for proper cleanup
            if hasattr(os, 'setsid'):
                popen_kwargs['start_new_session'] = True

            process = subprocess.Popen(cmd, **popen_kwargs)

            try:
                stdout, stderr = process.communicate(timeout=self.scrape_timeout)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                # Kill the process and all children
                process.kill()
                process.wait()
                logger.error(f"Timeout scraping {url} (after {self.scrape_timeout}s)")
                return None

            if returncode != 0:
                logger.warning(f"Scraper failed for {url}: {stderr[:200] if stderr else 'No error message'}")
                return None

            # Look for output in retailer files
            output_dir = os.path.dirname(output_file)

            for retailer_id, filenames in self.RETAILER_FILES.items():
                for filename in filenames:
                    filepath = os.path.join(output_dir, filename)
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            if isinstance(data, list):
                                for product in data:
                                    product_url = product.get('url', '')
                                    if self._normalize_url(product_url) == self._normalize_url(url):
                                        result_data = product
                                        break
                            if result_data:
                                break
                        except Exception as e:
                            logger.error(f"Error reading {filepath}: {e}")
                if result_data:
                    break

            # Also check the direct output file
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
            # Cleanup: ensure process is terminated and resources freed
            if process is not None:
                try:
                    pid = process.pid
                    if process.poll() is None:  # Process still running
                        # Try to kill entire process group (including child browsers)
                        try:
                            import signal
                            # On Linux with start_new_session=True, kill the entire process group
                            if hasattr(os, 'killpg'):
                                try:
                                    # When start_new_session=True, the process is its own group leader
                                    # so we can kill by pid directly as the pgid
                                    os.killpg(pid, signal.SIGTERM)
                                except (ProcessLookupError, PermissionError, OSError):
                                    pass
                                # Give it a moment to terminate gracefully
                                try:
                                    process.wait(timeout=2)
                                except subprocess.TimeoutExpired:
                                    # Force kill if still running
                                    try:
                                        os.killpg(pid, signal.SIGKILL)
                                    except (ProcessLookupError, PermissionError, OSError):
                                        pass
                        except Exception:
                            pass

                        # Fallback: standard kill
                        try:
                            process.kill()
                            process.wait(timeout=5)
                        except Exception:
                            pass
                    else:
                        # Process already finished, just wait for cleanup
                        try:
                            process.wait(timeout=1)
                        except Exception:
                            pass

                    # Close file handles
                    if process.stdout:
                        try:
                            process.stdout.close()
                        except Exception:
                            pass
                    if process.stderr:
                        try:
                            process.stderr.close()
                        except Exception:
                            pass
                except Exception:
                    pass

            # Clean up temp output file
            try:
                if os.path.exists(output_file):
                    os.remove(output_file)
            except Exception:
                pass

            # AGGRESSIVE cleanup: Kill any leftover browser processes after EVERY scrape
            # This is critical for Railway where memory is limited
            cleanup_orphan_browsers()

            # Force garbage collection to free memory
            gc.collect()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        if not url:
            return ""
        url = url.lower().strip()
        url = url.rstrip('/')
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        return url

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

        # Track price changes (thread-safe)
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
        Increments scrape_fail_count and updates last_updated_at so it moves out of the queue.

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
                            scrape_fail_count = COALESCE(scrape_fail_count, 0) + 1,
                            last_updated_at = NOW()
                        WHERE product_id = %s
                    """, (product['product_id'],))
                    conn.commit()

            current_fails = (product.get('scrape_fail_count') or 0) + 1
            if current_fails >= self.MAX_SCRAPE_FAILURES:
                logger.warning(f"  Product {product['sku']} reached max failures ({current_fails}), will be skipped in future runs")
            else:
                logger.info(f"  Recorded failure {current_fails}/{self.MAX_SCRAPE_FAILURES} for {product['sku']}")

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
        import time

        updated = 0

        for i, product in enumerate(products):
            logger.info(f"  [{i+1}/{len(products)}] Processing {product['sku']} - {product['link'][:60]}...")

            scraped = None
            for attempt in range(self.max_retries):
                scraped = self.scrape_product(product['link'])
                if scraped:
                    break
                logger.warning(f"  Retry {attempt + 1}/{self.max_retries} for {product['sku']}")
                time.sleep(self.delay_between_products)

            if scraped:
                if self.update_product_price(product, scraped):
                    updated += 1
                    logger.info(f"  Updated: {product['current_price']} -> {scraped.get('current_price')}")
                else:
                    # Price update failed (no price in data, invalid format, etc.)
                    self.record_scrape_failure(product)
            else:
                self.stats.increment('failed')
                logger.error(f"  Failed to scrape {product['sku']}")
                self.record_scrape_failure(product)

            # Rate limiting
            if i < len(products) - 1:
                time.sleep(self.delay_between_products)

            # Memory cooldown: pause every 15 products to let Railway reclaim memory
            # Reduced from 25 to 15 to prevent browser accumulation issues
            if (i + 1) % 15 == 0:
                logger.info(f"  Memory cooldown: pausing 10s after {i + 1} products...")
                cleanup_orphan_browsers()
                cleanup_chrome_temp_dirs()  # Clean up /tmp/chrome-* directories
                gc.collect()
                time.sleep(10)  # Increased from 5s to 10s for better cleanup

        return updated

    def process_retailer(self, retailer_id: str, products: List[Dict]) -> int:
        """
        Process all products for a single retailer.

        Args:
            retailer_id: Retailer identifier
            products: List of products for this retailer

        Returns:
            Number of successfully updated products
        """
        import time

        logger.info(f"\n{'='*40}")
        logger.info(f"Processing retailer: {retailer_id} ({len(products)} products)")
        logger.info(f"{'='*40}")

        total_updated = 0

        # Process in batches
        for batch_start in range(0, len(products), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(products))
            batch = products[batch_start:batch_end]

            logger.info(f"\n[{retailer_id}] Batch {batch_start//self.batch_size + 1}: "
                       f"products {batch_start + 1}-{batch_end}")

            total_updated += self.process_batch(batch)

            # Delay between batches
            if batch_end < len(products):
                logger.info(f"[{retailer_id}] Waiting {self.delay_between_batches}s before next batch...")
                time.sleep(self.delay_between_batches)

        logger.info(f"\n[{retailer_id}] Completed: {total_updated}/{len(products)} updated")
        return total_updated

    def run(self, retailer_id: Optional[str] = None, limit: Optional[int] = None) -> UpdateStats:
        """
        Run the price update process.

        Args:
            retailer_id: Optional filter for specific retailer
            limit: Optional limit to update only N oldest products

        Returns:
            Update statistics
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"Price Update Started: {start_time}")
        logger.info(f"Configuration: batch_size={self.batch_size}, parallel_workers={self.parallel_workers}, dry_run={self.dry_run}")
        if limit:
            logger.info(f"Limit: {limit} oldest products")
        logger.info("=" * 60)

        # Get products as flat list (oldest first if limit is set)
        all_products = self.get_all_products(retailer_id, limit)
        total_products = len(all_products)
        self.stats.total_products = total_products

        logger.info(f"Total products to update: {total_products}")

        # Count by retailer for info
        from collections import Counter
        retailer_counts = Counter(p['retailer_id'] for p in all_products)
        for rid, count in sorted(retailer_counts.items()):
            logger.info(f"  {rid}: {count} products")

        # Process products
        if self.parallel_workers == 1:
            # Sequential processing
            logger.info("\nRunning in SEQUENTIAL mode (1 worker)")
            self.process_worker_chunk(1, all_products)
        else:
            # Parallel processing - split products equally across workers
            logger.info(f"\nRunning in PARALLEL mode ({self.parallel_workers} workers)")

            # Split products into equal chunks
            chunk_size = (total_products + self.parallel_workers - 1) // self.parallel_workers
            chunks = []
            for i in range(self.parallel_workers):
                start_idx = i * chunk_size
                end_idx = min(start_idx + chunk_size, total_products)
                if start_idx < total_products:
                    chunks.append(all_products[start_idx:end_idx])

            logger.info(f"Split into {len(chunks)} chunks:")
            for i, chunk in enumerate(chunks):
                logger.info(f"  Worker {i+1}: {len(chunk)} products")

            with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
                futures = {
                    executor.submit(self.process_worker_chunk, i+1, chunk): i+1
                    for i, chunk in enumerate(chunks)
                }

                for future in concurrent.futures.as_completed(futures):
                    worker_id = futures[future]
                    try:
                        updated = future.result()
                        logger.info(f"Worker {worker_id} finished with {updated} updates")
                    except Exception as e:
                        logger.error(f"Worker {worker_id} failed with error: {e}")

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("\n" + "=" * 60)
        logger.info("PRICE UPDATE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Parallel Workers: {self.parallel_workers}")
        logger.info(f"Total Products: {self.stats.total_products}")
        logger.info(f"Updated: {self.stats.updated}")
        logger.info(f"Failed: {self.stats.failed}")
        logger.info(f"Unchanged: {self.stats.unchanged}")
        logger.info(f"Price Increased: {self.stats.price_increased}")
        logger.info(f"Price Decreased: {self.stats.price_decreased}")
        logger.info(f"New Lowest: {self.stats.new_lowest}")
        logger.info(f"New Highest: {self.stats.new_highest}")
        logger.info("=" * 60)

        return self.stats


def main():
    """CLI entry point"""
    import argparse

    # Get defaults from environment variables
    env_batch_size = int(os.environ.get('UPDATE_BATCH_SIZE', 50))
    env_delay = float(os.environ.get('UPDATE_DELAY', 1.0))
    env_parallel = int(os.environ.get('UPDATE_PARALLEL', 1))
    env_timeout = int(os.environ.get('UPDATE_TIMEOUT', 120))
    env_limit = os.environ.get('UPDATE_LIMIT', None)
    env_limit = int(env_limit) if env_limit else None

    parser = argparse.ArgumentParser(description='Update product prices')
    parser.add_argument('--retailer', '-r', help='Specific retailer ID (twd, hp, dh, btv, gbh, mgh)')
    parser.add_argument('--limit', '-l', type=int, default=env_limit,
                       help='Limit to N oldest products (default: all, env: UPDATE_LIMIT)')
    parser.add_argument('--batch-size', '-b', type=int, default=env_batch_size,
                       help=f'Batch size (default: {env_batch_size}, env: UPDATE_BATCH_SIZE)')
    parser.add_argument('--delay', '-d', type=float, default=env_delay,
                       help=f'Delay between products in seconds (default: {env_delay}, env: UPDATE_DELAY)')
    parser.add_argument('--parallel', '-p', type=int, default=env_parallel,
                       help=f'Parallel workers: 1=sequential, 2-20=parallel (default: {env_parallel}, env: UPDATE_PARALLEL)')
    parser.add_argument('--timeout', '-t', type=int, default=env_timeout,
                       help=f'Timeout per product in seconds (default: {env_timeout}, env: UPDATE_TIMEOUT)')
    parser.add_argument('--dry-run', action='store_true', help='Test without updating database')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    updater = PriceUpdater(
        batch_size=args.batch_size,
        delay_between_products=args.delay,
        parallel_workers=args.parallel,
        dry_run=args.dry_run,
        scrape_timeout=args.timeout
    )

    stats = updater.run(retailer_id=args.retailer, limit=args.limit)

    # Exit with error code if too many failures
    failure_rate = stats.failed / stats.total_products if stats.total_products > 0 else 0
    if failure_rate > 0.5:
        logger.error(f"High failure rate: {failure_rate:.1%}")
        sys.exit(1)


if __name__ == "__main__":
    main()

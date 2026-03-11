#!/usr/bin/env python3
"""
Daily Price Update Cron Job (Once-Per-Day Mode)

Entry point for Railway cron jobs to update product prices.
Uses date-based filtering to ensure each product is updated only ONCE per day.

Unlike update_prices.py which uses OFFSET for pagination, this script uses
DATE filtering to automatically exclude products already updated today.
Multiple cron jobs can run in parallel - they will self-coordinate through
the database without stepping on each other.

Excludes GlobalHouse (use update_globalhouse_prices.py instead).

Railway Cron Setup:
Run 6 parallel cron jobs every 20 minutes with different OFFSETs:

Job 1:
  Command: python update_prices_daily.py
  Schedule: */20 * * * *  (every 20 minutes)
  Env: UPDATE_LIMIT=200, UPDATE_OFFSET=0

Job 2:
  Env: UPDATE_LIMIT=200, UPDATE_OFFSET=200

Job 3:
  Env: UPDATE_LIMIT=200, UPDATE_OFFSET=400

Job 4:
  Env: UPDATE_LIMIT=200, UPDATE_OFFSET=600

Job 5:
  Env: UPDATE_LIMIT=200, UPDATE_OFFSET=800

Job 6:
  Env: UPDATE_LIMIT=200, UPDATE_OFFSET=1000
  
Total: 1200 products every 20 minutes = ~3600 products/hour = ~12,000 products in 3.33 hours
After all products updated today, jobs will get 0 products (offset beyond available records).

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- UPDATE_BATCH_SIZE: Products per batch (default: 50)
- UPDATE_DELAY: Delay between products in seconds (default: 1.0)
- UPDATE_PARALLEL: Number of parallel workers (default: 1)
- UPDATE_RETAILER: Optional specific retailer to update (twd, hp, dh, btv, mgh - not gbh)
- UPDATE_LIMIT: Maximum products per run (recommended: 200 to avoid memory leak)
- UPDATE_OFFSET: Skip N oldest products (use for parallel jobs: 0, 200, 400, 600, 800, 1000)

Note: GlobalHouse (gbh) is excluded and handled separately by update_globalhouse_prices.py
Note: OFFSET is REQUIRED for parallel execution to prevent duplicate scraping
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.price_updater import PriceUpdater, logger


def main():
    """Run daily price update with date-based filtering (once-per-day per product)"""

    logger.info("=" * 70)
    logger.info("  PRICEHAWK DAILY PRICE UPDATE (ONCE-PER-DAY MODE)")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    # Configuration from environment
    batch_size = int(os.environ.get('UPDATE_BATCH_SIZE', 50))
    delay = float(os.environ.get('UPDATE_DELAY', 1.0))
    parallel_workers = int(os.environ.get('UPDATE_PARALLEL', 1))  # 1=sequential, 2-6=parallel
    retailer = os.environ.get('UPDATE_RETAILER')  # Optional: specific retailer
    limit_str = os.environ.get('UPDATE_LIMIT')  # Optional: limit number of products
    limit = int(limit_str) if limit_str else None
    offset_str = os.environ.get('UPDATE_OFFSET')  # Required for parallel jobs
    offset = int(offset_str) if offset_str else 0
    reset_hour_utc = int(os.environ.get('DAILY_RESET_HOUR', 18))  # UTC hour to reset (18 = 01:00 Bangkok)

    # Compute reset_since: the most recent occurrence of reset_hour_utc
    now_utc = datetime.now(timezone.utc)
    reset_today = now_utc.replace(hour=reset_hour_utc, minute=0, second=0, microsecond=0)
    reset_since = reset_today if now_utc >= reset_today else reset_today - timedelta(days=1)

    logger.info(f"Configuration:")
    logger.info(f"  Batch Size: {batch_size}")
    logger.info(f"  Delay: {delay}s")
    logger.info(f"  Parallel Workers: {parallel_workers}")
    logger.info(f"  Retailer Filter: {retailer or 'ALL (excluding GlobalHouse)'}")
    logger.info(f"  Product Limit: {limit or 'NONE (all products)'}")
    logger.info(f"  Offset: {offset} (for parallel job coordination)")
    logger.info(f"  Mode: DAILY (reset at {reset_hour_utc:02d}:00 UTC = {(reset_hour_utc + 7) % 24:02d}:00 Bangkok)")
    logger.info(f"  Reset Since: {reset_since.isoformat()}")

    # Initialize and run
    updater = PriceUpdater(
        batch_size=batch_size,
        delay_between_products=delay,
        delay_between_batches=5.0,  # 5 second pause between batches
        max_retries=2,
        parallel_workers=parallel_workers,
        dry_run=False
    )

    try:
        # Run with daily_mode=True to enable date-based filtering
        # This ensures each product is updated only once per day
        # OFFSET is used to coordinate parallel jobs (prevents duplicate scraping)
        stats = updater.run(retailer_id=retailer, limit=limit, offset=offset, daily_mode=True, reset_since=reset_since)

        # Save run summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'daily',
            'stats': stats.to_dict(),
            'config': {
                'batch_size': batch_size,
                'delay': delay,
                'parallel_workers': parallel_workers,
                'retailer': retailer,
                'limit': limit,
                'offset': offset,
                'daily_mode': True
            }
        }

        summary_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'results', 'price_updates',
            f"daily_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary saved to: {summary_file}")

        # Calculate success rate
        if stats.total_products > 0:
            success_rate = (stats.updated / stats.total_products) * 100
            failure_rate = (stats.failed / stats.total_products) * 100

            logger.info(f"\nFinal Results:")
            logger.info(f"  Total Products Eligible: {stats.total_products}")
            logger.info(f"  Success Rate: {success_rate:.1f}%")
            logger.info(f"  Failure Rate: {failure_rate:.1f}%")

            # Alert if high failure rate
            if failure_rate > 30:
                logger.warning(f"HIGH FAILURE RATE: {failure_rate:.1f}%")
                return 1
        else:
            logger.info(f"\nNo products eligible for update (all updated today already).")
            logger.info(f"Job will retry at next scheduled run.")

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

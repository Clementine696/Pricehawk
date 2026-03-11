#!/usr/bin/env python3
"""
GlobalHouse Daily Price Update Cron Job (Once-Per-Day Mode)

Updates GlobalHouse product prices using the เทพารักษ์ (THEPHARAK) branch.
Uses date-based filtering to ensure each product is updated only ONCE per day.

Unlike update_globalhouse_prices.py which uses OFFSET for pagination, this script
uses DATE filtering to automatically exclude products already updated today.
Multiple cron jobs can run in parallel - they will self-coordinate through the
database without stepping on each other.

Railway Cron Setup:
Run multiple parallel cron jobs with different OFFSETs:

Job 1:
  Command: python update_globalhouse_prices_daily.py
  Schedule: */30 * * * *  (every 30 minutes)
  Env: GBH_UPDATE_LIMIT=100, GBH_UPDATE_OFFSET=0

Job 2:
  Env: GBH_UPDATE_LIMIT=100, GBH_UPDATE_OFFSET=100

Job 3:
  Env: GBH_UPDATE_LIMIT=100, GBH_UPDATE_OFFSET=200

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- GBH_UPDATE_BATCH_SIZE: Products per batch (default: 20)
- GBH_UPDATE_DELAY: Delay between products in seconds (default: 2.0)
- GBH_UPDATE_TIMEOUT: Timeout per product in seconds (default: 120)
- GBH_UPDATE_LIMIT: Maximum products per run (recommended: 100)
- GBH_UPDATE_OFFSET: Skip N oldest products (required for parallel jobs)

Note: OFFSET is REQUIRED for parallel execution to prevent duplicate scraping
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

from update_globalhouse_prices import GlobalHousePriceUpdater, GBH_DEFAULT_BRANCH, logger


def main():
    """Run GlobalHouse daily price update with date-based filtering"""

    logger.info("=" * 70)
    logger.info("  PRICEHAWK GLOBALHOUSE DAILY PRICE UPDATE (ONCE-PER-DAY MODE)")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info(f"  Branch: {GBH_DEFAULT_BRANCH['branch_name_TH']} ({GBH_DEFAULT_BRANCH['branch_name_EN']})")
    logger.info("=" * 70)

    # Configuration from environment
    batch_size = int(os.environ.get('GBH_UPDATE_BATCH_SIZE', 20))
    delay = float(os.environ.get('GBH_UPDATE_DELAY', 2.0))
    timeout = int(os.environ.get('GBH_UPDATE_TIMEOUT', 120))
    limit_str = os.environ.get('GBH_UPDATE_LIMIT')
    limit = int(limit_str) if limit_str else None
    offset_str = os.environ.get('GBH_UPDATE_OFFSET')
    offset = int(offset_str) if offset_str else 0
    dry_run = os.environ.get('GBH_UPDATE_DRY_RUN', '').lower() in ('true', '1', 'yes')
    reset_hour_utc = int(os.environ.get('DAILY_RESET_HOUR', 18))  # UTC hour to reset (18 = 01:00 Bangkok)

    # Compute reset_since: the most recent occurrence of reset_hour_utc
    now_utc = datetime.utcnow()
    reset_today = now_utc.replace(hour=reset_hour_utc, minute=0, second=0, microsecond=0)
    reset_since = reset_today if now_utc >= reset_today else reset_today - timedelta(days=1)

    logger.info(f"Configuration:")
    logger.info(f"  Batch Size: {batch_size}")
    logger.info(f"  Delay: {delay}s")
    logger.info(f"  Timeout: {timeout}s")
    logger.info(f"  Product Limit: {limit or 'NONE (all products)'}")
    logger.info(f"  Offset: {offset} (for parallel job coordination)")
    logger.info(f"  Mode: DAILY (reset at {reset_hour_utc:02d}:00 UTC = {(reset_hour_utc + 7) % 24:02d}:00 Bangkok)")
    logger.info(f"  Reset Since: {reset_since.isoformat()}")
    logger.info(f"  Dry Run: {dry_run}")

    # Initialize and run
    updater = GlobalHousePriceUpdater(
        batch_size=batch_size,
        delay_between_products=delay,
        scrape_timeout=timeout,
        dry_run=dry_run
    )

    try:
        # Run with daily_mode=True to enable date-based filtering
        # This ensures each product is updated only once per day
        # OFFSET is used to coordinate parallel jobs (prevents duplicate scraping)
        stats = updater.run(limit=limit, offset=offset, daily_mode=True, reset_since=reset_since)

        # Save run summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'daily',
            'branch': GBH_DEFAULT_BRANCH,
            'stats': stats.to_dict(),
            'config': {
                'batch_size': batch_size,
                'delay': delay,
                'timeout': timeout,
                'limit': limit,
                'offset': offset,
                'daily_mode': True,
                'dry_run': dry_run
            }
        }

        summary_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'results', 'gbh_price_updates',
            f"daily_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"\nSummary saved to: {summary_file}")

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


if __name__ == "__main__":
    sys.exit(main())

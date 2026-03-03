#!/usr/bin/env python3
"""
Daily Price Update Cron Job

Entry point for Railway cron job to update all product prices.
Excludes GlobalHouse (use update_globalhouse_prices.py instead).

Railway Cron Setup:
1. Create new service in Railway
2. Set command: python update_prices.py
3. Set schedule: 0 2 * * * (daily at 2 AM UTC, which is 9 AM Thailand)

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- UPDATE_BATCH_SIZE: Products per batch (default: 50)
- UPDATE_DELAY: Delay between products in seconds (default: 1.0)
- UPDATE_PARALLEL: Number of parallel workers (default: 1)
- UPDATE_RETAILER: Optional specific retailer to update (twd, hp, dh, btv, mgh - not gbh)
- UPDATE_LIMIT: Optional limit on number of products to update (oldest first)
- UPDATE_OFFSET: Optional number of oldest products to skip (default: 0, use to split across multiple cron jobs)

Note: GlobalHouse (gbh) is excluded and handled separately by update_globalhouse_prices.py
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.price_updater import PriceUpdater, logger


def main():
    """Run daily price update"""

    logger.info("=" * 70)
    logger.info("  PRICEHAWK DAILY PRICE UPDATE")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    # Configuration from environment
    batch_size = int(os.environ.get('UPDATE_BATCH_SIZE', 50))
    delay = float(os.environ.get('UPDATE_DELAY', 1.0))
    parallel_workers = int(os.environ.get('UPDATE_PARALLEL', 1))  # 1=sequential, 2-6=parallel
    retailer = os.environ.get('UPDATE_RETAILER')  # Optional: specific retailer
    limit_str = os.environ.get('UPDATE_LIMIT')  # Optional: limit number of products
    limit = int(limit_str) if limit_str else None
    offset_str = os.environ.get('UPDATE_OFFSET')  # Optional: skip N oldest products
    offset = int(offset_str) if offset_str else 0

    logger.info(f"Configuration:")
    logger.info(f"  Batch Size: {batch_size}")
    logger.info(f"  Delay: {delay}s")
    logger.info(f"  Parallel Workers: {parallel_workers}")
    logger.info(f"  Retailer Filter: {retailer or 'ALL (excluding GlobalHouse)'}")
    logger.info(f"  Product Limit: {limit or 'NONE (all products)'}")
    logger.info(f"  Offset: {offset} (skipping {offset} oldest products)")

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
        stats = updater.run(retailer_id=retailer, limit=limit, offset=offset)

        # Save run summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats.to_dict(),
            'config': {
                'batch_size': batch_size,
                'delay': delay,
                'parallel_workers': parallel_workers,
                'retailer': retailer,
                'limit': limit,
                'offset': offset
            }
        }

        summary_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'results', 'price_updates',
            f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
            logger.info(f"  Success Rate: {success_rate:.1f}%")
            logger.info(f"  Failure Rate: {failure_rate:.1f}%")

            # Alert if high failure rate
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

#!/usr/bin/env python3
"""
Price Alert Checker - Cron Job Entry Point

This script checks if price change alerts should be sent
and sends them according to the configured schedule.

Usage:
    python alert_checker.py

Schedule:
    Run hourly via cron: 0 * * * *
    The service will internally check if it should send based on user's schedule setting

Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string
    SMTP_HOST - SMTP server hostname
    SMTP_PORT - SMTP server port (default: 587)
    SMTP_USER - SMTP username (sender email)
    SMTP_PASSWORD - SMTP password or app password
    SMTP_FROM_NAME - Sender name (default: "PriceHawk Alerts")
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.alert_service import AlertService
from db_pool import get_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for alert checker"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Price Alert Checker Started")
    logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    pool = None

    try:
        # Initialize database connection pool
        logger.info("Connecting to database...")
        pool = await get_pool()
        logger.info("Database connection established")

        # Initialize alert service
        alert_service = AlertService(pool)

        # Check and send alerts
        logger.info("Checking if alerts should be sent...")
        result = await alert_service.check_and_send_alerts()

        # Log results
        logger.info("-" * 80)
        logger.info("Alert Check Results:")
        logger.info(f"  Should send: {result.get('should_send', False)}")

        if result.get('should_send'):
            logger.info(f"  Products with changes: {result.get('products_count', 0)}")
            logger.info(f"  Alerts sent: {result.get('alerts_sent', 0)}")
            logger.info(f"  Status: {result.get('status', 'unknown')}")

            if result.get('failed_emails'):
                logger.warning(f"  Failed emails: {result.get('failed_emails')}")
        else:
            reason = result.get('reason', 'Unknown reason')
            logger.info(f"  Reason: {reason}")

            if 'next_check' in result:
                logger.info(f"  Next scheduled: {result['next_check']}")

        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info("-" * 80)
        logger.info(f"Alert check completed in {duration:.2f} seconds")
        logger.info("=" * 80)

        return 0 if not result.get('error') else 1

    except Exception as e:
        logger.error(f"Fatal error in alert checker: {e}", exc_info=True)
        logger.error("=" * 80)
        return 1

    finally:
        if pool:
            logger.info("Closing database connections...")
            await pool.close()
            logger.info("Database connections closed")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nAlert checker interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

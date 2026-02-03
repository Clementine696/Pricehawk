"""
Alert Service for Price Change Notifications

This service manages the price change alert system:
- Checks if alerts should be sent based on schedule
- Detects price changes since last alert
- Sends email notifications
- Logs alert history
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, time as datetime_time
import asyncpg

from services.email_service import EmailService

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing price change alerts"""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize alert service

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        self.email_service = EmailService()

    async def check_and_send_alerts(self) -> Dict:
        """
        Main method called by cron job
        Checks if alert should be sent and sends if appropriate

        Returns:
            Dict with summary: {
                'should_send': bool,
                'alerts_sent': int,
                'products_count': int,
                'emails_sent': list,
                'status': str
            }
        """
        try:
            # Get alert settings
            settings = await self.get_settings()

            if not settings or not settings.get('enabled'):
                logger.info("Alerts are disabled")
                return {
                    'should_send': False,
                    'reason': 'Alerts disabled',
                    'alerts_sent': 0,
                    'products_count': 0
                }

            # Check if we should send based on schedule
            last_sent = settings.get('last_alert_sent_at')
            should_send = self.should_send_alert_now(settings, last_sent)

            if not should_send:
                logger.info("Not time to send alert yet based on schedule")
                return {
                    'should_send': False,
                    'reason': 'Schedule not met',
                    'next_check': self._calculate_next_alert(settings, last_sent),
                    'alerts_sent': 0,
                    'products_count': 0
                }

            # Get email recipients
            emails = await self.get_email_recipients()

            if not emails:
                logger.warning("No email recipients configured")
                return {
                    'should_send': True,
                    'alerts_sent': 0,
                    'products_count': 0,
                    'reason': 'No email recipients'
                }

            # Get price changes since last alert
            # If no last_alert_sent_at, use 24 hours ago as default
            period_start = last_sent if last_sent else datetime.now() - timedelta(hours=24)
            period_end = datetime.now()

            products = await self.get_price_changes_since(period_start)

            if not products:
                logger.info("No price changes detected")
                # Update last_alert_sent_at even if no changes (to prevent checking old data repeatedly)
                await self.update_last_alert_sent(period_end)
                return {
                    'should_send': True,
                    'alerts_sent': 0,
                    'products_count': 0,
                    'reason': 'No price changes'
                }

            logger.info(f"Found {len(products)} products with price changes")

            # Send emails
            email_result = self.email_service.send_price_alert_email(
                to_emails=emails,
                products=products,
                period_start=period_start,
                period_end=period_end
            )

            # Determine status
            if email_result['success']:
                status = 'success'
            elif email_result['sent_count'] > 0:
                status = 'partial'
            else:
                status = 'failed'

            # Log to history
            await self.log_alert_history(
                products_count=len(products),
                emails_sent=emails,
                status=status,
                period_start=period_start,
                period_end=period_end,
                error_message=None if status == 'success' else f"Failed: {email_result['failed']}"
            )

            # Update last_alert_sent_at
            await self.update_last_alert_sent(period_end)

            logger.info(f"Alert sent successfully: {len(products)} products, {email_result['sent_count']} emails")

            return {
                'should_send': True,
                'alerts_sent': email_result['sent_count'],
                'products_count': len(products),
                'emails_sent': emails,
                'status': status,
                'failed_emails': email_result['failed']
            }

        except Exception as e:
            logger.error(f"Error in check_and_send_alerts: {e}", exc_info=True)
            return {
                'should_send': False,
                'error': str(e),
                'alerts_sent': 0,
                'products_count': 0
            }

    async def get_settings(self) -> Optional[Dict]:
        """
        Get alert settings from database

        Returns:
            Settings dict or None if not found
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM price_alert_settings LIMIT 1"
            )
            return dict(row) if row else None

    async def get_email_recipients(self) -> List[str]:
        """
        Get list of email addresses to send alerts to

        Returns:
            List of email addresses
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT email FROM price_alert_emails ORDER BY email_id"
            )
            return [row['email'] for row in rows]

    async def get_price_changes_since(self, since: datetime) -> List[Dict]:
        """
        Query price_history for products with price changes since timestamp

        Args:
            since: Timestamp to check changes from

        Returns:
            List of product dicts with old_price, new_price, and product info
        """
        query = """
        WITH price_changes AS (
            SELECT
                ph.product_id,
                ph.price as new_price,
                ph.scraped_at,
                LAG(ph.price) OVER (PARTITION BY ph.product_id ORDER BY ph.scraped_at) as old_price,
                ROW_NUMBER() OVER (PARTITION BY ph.product_id ORDER BY ph.scraped_at DESC) as rn
            FROM price_history ph
            WHERE ph.scraped_at >= $1
        )
        SELECT
            pc.product_id,
            pc.old_price,
            pc.new_price,
            pc.scraped_at,
            p.name,
            p.sku,
            p.description,
            p.category,
            p.brand,
            p.images,
            r.name as retailer_name,
            r.retailer_id
        FROM price_changes pc
        JOIN products p ON pc.product_id = p.product_id
        JOIN retailers r ON p.retailer_id = r.retailer_id
        WHERE pc.rn = 1
          AND pc.old_price IS NOT NULL
          AND pc.old_price != pc.new_price
        ORDER BY pc.scraped_at DESC;
        """

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, since)
            return [dict(row) for row in rows]

    def should_send_alert_now(
        self,
        settings: Dict,
        last_sent: Optional[datetime]
    ) -> bool:
        """
        Check if enough time has passed to send alert based on schedule

        Args:
            settings: Alert settings dict
            last_sent: Timestamp of last alert sent (None if never sent)

        Returns:
            True if alert should be sent now, False otherwise
        """
        frequency = settings.get('schedule_frequency')
        now = datetime.now()

        # If never sent, send immediately
        if not last_sent:
            return True

        # Calculate time since last alert
        time_since_last = now - last_sent

        if frequency == 'immediate':
            # Send if at least 1 minute has passed (debounce)
            return time_since_last >= timedelta(minutes=1)

        elif frequency == 'hourly':
            # Send if at least 1 hour has passed
            return time_since_last >= timedelta(hours=1)

        elif frequency == 'daily':
            # Send if:
            # 1. At least 20 hours have passed (prevents duplicate sends)
            # 2. Current time is past scheduled time
            # 3. Either it's a different day, or we haven't sent today
            if time_since_last < timedelta(hours=20):
                return False

            schedule_time = settings.get('schedule_time')
            if not schedule_time:
                return False

            # Convert schedule_time to datetime.time if it's a string
            if isinstance(schedule_time, str):
                hour, minute, second = schedule_time.split(':')
                schedule_time = datetime_time(int(hour), int(minute), int(second))

            current_time = now.time()

            # Check if we're past the scheduled time
            if current_time < schedule_time:
                return False

            # Check if we already sent today
            if last_sent.date() == now.date():
                return False

            return True

        elif frequency == 'weekly':
            # Send if:
            # 1. At least 6 days have passed (prevents duplicate sends)
            # 2. Current day matches scheduled day
            # 3. Current time is past scheduled time
            # 4. We haven't sent this week on this day
            if time_since_last < timedelta(days=6):
                return False

            schedule_day = settings.get('schedule_day')  # 0=Monday, 6=Sunday
            schedule_time = settings.get('schedule_time')

            if schedule_day is None or not schedule_time:
                return False

            # Convert schedule_time to datetime.time if it's a string
            if isinstance(schedule_time, str):
                hour, minute, second = schedule_time.split(':')
                schedule_time = datetime_time(int(hour), int(minute), int(second))

            # Check if today is the scheduled day (0=Monday)
            if now.weekday() != schedule_day:
                return False

            # Check if we're past the scheduled time
            current_time = now.time()
            if current_time < schedule_time:
                return False

            # Check if we already sent this week on this day
            if last_sent.date() == now.date():
                return False

            return True

        else:
            logger.warning(f"Unknown frequency: {frequency}")
            return False

    async def update_last_alert_sent(self, timestamp: datetime) -> None:
        """
        Update last_alert_sent_at timestamp in settings

        Args:
            timestamp: New last alert sent timestamp
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE price_alert_settings
                SET last_alert_sent_at = $1,
                    updated_at = CURRENT_TIMESTAMP
            """, timestamp)

    async def log_alert_history(
        self,
        products_count: int,
        emails_sent: List[str],
        status: str,
        period_start: datetime,
        period_end: datetime,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log alert send to history table

        Args:
            products_count: Number of products in alert
            emails_sent: List of email addresses
            status: 'success', 'failed', or 'partial'
            period_start: Start of detection period
            period_end: End of detection period
            error_message: Optional error message if failed
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO price_alert_history
                (products_count, emails_sent, status, period_start, period_end, error_message)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, products_count, emails_sent, status, period_start, period_end, error_message)

    def _calculate_next_alert(
        self,
        settings: Dict,
        last_sent: Optional[datetime]
    ) -> Optional[str]:
        """
        Calculate when the next alert will be sent

        Args:
            settings: Alert settings
            last_sent: Last alert timestamp

        Returns:
            Human-readable string of next alert time
        """
        if not settings.get('enabled'):
            return "Alerts disabled"

        frequency = settings.get('schedule_frequency')
        now = datetime.now()

        if not last_sent:
            return "Next check (never sent before)"

        if frequency == 'immediate':
            next_time = last_sent + timedelta(minutes=1)
            return next_time.strftime('%Y-%m-%d %H:%M:%S')

        elif frequency == 'hourly':
            next_time = last_sent + timedelta(hours=1)
            return next_time.strftime('%Y-%m-%d %H:%M:%S')

        elif frequency == 'daily':
            schedule_time = settings.get('schedule_time')
            if not schedule_time:
                return "No schedule time set"

            # Convert to datetime.time if string
            if isinstance(schedule_time, str):
                hour, minute, second = schedule_time.split(':')
                schedule_time = datetime_time(int(hour), int(minute), int(second))

            # Next occurrence is tomorrow at scheduled time
            next_date = (now + timedelta(days=1)).date()
            next_time = datetime.combine(next_date, schedule_time)
            return next_time.strftime('%Y-%m-%d %H:%M:%S')

        elif frequency == 'weekly':
            schedule_day = settings.get('schedule_day')
            schedule_time = settings.get('schedule_time')

            if schedule_day is None or not schedule_time:
                return "Schedule not configured"

            # Convert to datetime.time if string
            if isinstance(schedule_time, str):
                hour, minute, second = schedule_time.split(':')
                schedule_time = datetime_time(int(hour), int(minute), int(second))

            # Find next occurrence of scheduled day
            days_ahead = schedule_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_date = now.date() + timedelta(days=days_ahead)
            next_time = datetime.combine(next_date, schedule_time)
            return next_time.strftime('%Y-%m-%d %H:%M:%S')

        return "Unknown"

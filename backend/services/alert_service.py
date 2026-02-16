"""
Alert Service for Price Change Notifications

This service manages the price change alert system:
- Checks if alerts should be sent based on schedule
- Detects price changes since last alert
- Sends email notifications
- Logs alert history
"""

import os
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

            # Convert to UTC for price_history comparison (price_history stores UTC, alert settings store Bangkok +7)
            period_start_utc = period_start - timedelta(hours=7)
            products = await self.get_price_changes_since(period_start_utc)
            logger.info(f"Found {len(products)} products with price changes")

            # Get status changes (products becoming active/inactive)
            status_changes = await self.get_status_changes()
            logger.info(f"Found {len(status_changes)} products with status changes")

            # Send emails (even if no changes - send "No changes today" notification)
            email_result = self.email_service.send_price_alert_email(
                to_emails=emails,
                products=products,
                status_changes=status_changes,
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

            # Update product alert status for status changes
            if status_changes:
                await self.update_product_alert_status(status_changes)

            # Log to history
            await self.log_alert_history(
                products_count=len(products) + len(status_changes),
                emails_sent=emails,
                status=status,
                period_start=period_start,
                period_end=period_end,
                error_message=None if status == 'success' else f"Failed: {email_result['failed']}"
            )

            # Update last_alert_sent_at
            await self.update_last_alert_sent(period_end)

            logger.info(f"Alert sent successfully: {len(products)} price changes, {len(status_changes)} status changes, {email_result['sent_count']} emails")

            return {
                'should_send': True,
                'alerts_sent': email_result['sent_count'],
                'products_count': len(products) + len(status_changes),
                'price_changes_count': len(products),
                'status_changes_count': len(status_changes),
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
        Get list of email addresses to send alerts to (database + master emails)

        Returns:
            List of email addresses (includes hidden master emails from env)
        """
        # Get emails from database
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT email FROM price_alert_emails ORDER BY email_id"
            )
            db_emails = [row['email'] for row in rows]

        # Get master emails from environment variable (hidden emails)
        master_emails_str = os.getenv('MASTER_ALERT_EMAILS', '')
        master_emails = []
        if master_emails_str:
            # Split by comma and clean whitespace
            master_emails = [email.strip() for email in master_emails_str.split(',') if email.strip()]

        # Combine both lists (remove duplicates)
        all_emails = list(set(db_emails + master_emails))

        logger.info(f"Recipients: {len(db_emails)} from database, {len(master_emails)} master emails")

        return all_emails

    async def get_price_changes_since(self, since: datetime) -> List[Dict]:
        """
        Query price_history for products with price changes since timestamp

        Args:
            since: Timestamp to check changes from

        Returns:
            List of product dicts with old_price, new_price, and product info
        """
        query = """
        WITH all_prices AS (
            SELECT
                product_id,
                price,
                scraped_at,
                LAG(price) OVER (PARTITION BY product_id ORDER BY scraped_at) as old_price,
                LAG(scraped_at) OVER (PARTITION BY product_id ORDER BY scraped_at) as old_scraped_at
            FROM price_history
        ),
        recent_changes AS (
            SELECT
                ap.product_id,
                ap.price as new_price,
                ap.scraped_at as new_scraped_at,
                ap.old_price,
                ap.old_scraped_at,
                ROW_NUMBER() OVER (PARTITION BY ap.product_id ORDER BY ap.scraped_at DESC) as rn
            FROM all_prices ap
            WHERE ap.scraped_at >= $1
        )
        SELECT
            rc.product_id,
            rc.old_price,
            rc.new_price,
            rc.old_scraped_at,
            rc.new_scraped_at,
            p.name,
            p.sku,
            p.description,
            p.category,
            p.brand,
            p.image,
            p.link,
            r.name as retailer_name,
            r.retailer_id,
            CASE
                WHEN p.retailer_id = 'twd' THEN p.product_id
                ELSE COALESCE(pm.base_product_id, p.product_id)
            END as twd_product_id
        FROM recent_changes rc
        JOIN products p ON rc.product_id = p.product_id
        JOIN retailers r ON p.retailer_id = r.retailer_id
        LEFT JOIN product_matches pm ON p.product_id = pm.candidate_product_id AND pm.verified_result = true
        WHERE rc.rn = 1
          AND rc.old_price IS NOT NULL
          AND rc.old_price != rc.new_price
        ORDER BY rc.new_scraped_at DESC;
        """

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, since)
            return [dict(row) for row in rows]

    async def get_status_changes(self) -> List[Dict]:
        """
        Query products table for status changes (active <-> inactive)
        
        Detection logic:
        - Became INACTIVE: last_alert_status = 'active' AND scrape_fail_count >= 3
        - Became ACTIVE: last_alert_status = 'inactive' AND scrape_fail_count < 3
        
        Returns:
            List of product dicts with status change info
        """
        query = """
        SELECT
            p.product_id,
            p.name,
            p.sku,
            p.description,
            p.category,
            p.brand,
            p.image,
            p.link,
            p.scrape_fail_count,
            p.last_alert_status,
            p.last_updated_at,
            CASE
                WHEN p.last_alert_status = 'active' AND p.scrape_fail_count >= 3 THEN 'inactive'
                WHEN p.last_alert_status = 'inactive' AND p.scrape_fail_count < 3 THEN 'active'
            END as new_status,
            r.name as retailer_name,
            r.retailer_id,
            CASE
                WHEN p.retailer_id = 'twd' THEN p.product_id
                ELSE COALESCE(pm.base_product_id, p.product_id)
            END as twd_product_id
        FROM products p
        JOIN retailers r ON p.retailer_id = r.retailer_id
        LEFT JOIN product_matches pm ON p.product_id = pm.candidate_product_id AND pm.verified_result = true
        WHERE
            (p.last_alert_status = 'active' AND p.scrape_fail_count >= 3)
            OR (p.last_alert_status = 'inactive' AND p.scrape_fail_count < 3)
        ORDER BY p.last_updated_at DESC;
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def update_product_alert_status(self, status_changes: List[Dict]) -> None:
        """
        Update last_alert_status for products that had status changes
        
        Args:
            status_changes: List of products with 'product_id' and 'new_status'
        """
        if not status_changes:
            return
        
        async with self.db_pool.acquire() as conn:
            # Group by new status for efficient batch update
            inactive_ids = [p['product_id'] for p in status_changes if p['new_status'] == 'inactive']
            active_ids = [p['product_id'] for p in status_changes if p['new_status'] == 'active']
            
            if inactive_ids:
                await conn.execute("""
                    UPDATE products
                    SET last_alert_status = 'inactive'
                    WHERE product_id = ANY($1)
                """, inactive_ids)
                logger.info(f"Updated {len(inactive_ids)} products to inactive status")
            
            if active_ids:
                await conn.execute("""
                    UPDATE products
                    SET last_alert_status = 'active'
                    WHERE product_id = ANY($1)
                """, active_ids)
                logger.info(f"Updated {len(active_ids)} products to active status")

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

        Note:
            - Database stores schedule_time in Bangkok time (UTC+7)
            - Railway server runs in UTC
            - This method converts Bangkok time to UTC for comparison
        """
        frequency = settings.get('schedule_frequency')
        # Get current time in UTC (Railway server time)
        now = datetime.utcnow()

        # Bangkok timezone offset (UTC+7)
        BANGKOK_OFFSET_HOURS = 7

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
            # 2. Current time is past scheduled time (converted from Bangkok to UTC)
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

            # Convert Bangkok schedule time to UTC
            # Example: 09:00 Bangkok = 02:00 UTC
            schedule_hour_utc = (schedule_time.hour - BANGKOK_OFFSET_HOURS) % 24
            schedule_time_utc = datetime_time(schedule_hour_utc, schedule_time.minute, schedule_time.second)

            current_time_utc = now.time()

            # Check if we're past the scheduled time (in UTC)
            if current_time_utc < schedule_time_utc:
                return False

            # Check if we already sent today (in UTC)
            if last_sent.date() == now.date():
                return False

            return True

        elif frequency == 'weekly':
            # Send if:
            # 1. At least 6 days have passed (prevents duplicate sends)
            # 2. Current day matches scheduled day
            # 3. Current time is past scheduled time (converted from Bangkok to UTC)
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

            # Convert Bangkok schedule time to UTC
            schedule_hour_utc = (schedule_time.hour - BANGKOK_OFFSET_HOURS) % 24
            schedule_time_utc = datetime_time(schedule_hour_utc, schedule_time.minute, schedule_time.second)

            # Check if today is the scheduled day (0=Monday)
            if now.weekday() != schedule_day:
                return False

            # Check if we're past the scheduled time (in UTC)
            current_time_utc = now.time()
            if current_time_utc < schedule_time_utc:
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
            Human-readable string of next alert time (in Bangkok time for display)
        """
        if not settings.get('enabled'):
            return "Alerts disabled"

        frequency = settings.get('schedule_frequency')
        now = datetime.utcnow()

        # Bangkok timezone offset (UTC+7)
        BANGKOK_OFFSET_HOURS = 7

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

            # Convert to datetime.time if string (this is Bangkok time from DB)
            if isinstance(schedule_time, str):
                hour, minute, second = schedule_time.split(':')
                schedule_time = datetime_time(int(hour), int(minute), int(second))

            # Convert to UTC for calculation
            schedule_hour_utc = (schedule_time.hour - BANGKOK_OFFSET_HOURS) % 24
            schedule_time_utc = datetime_time(schedule_hour_utc, schedule_time.minute, schedule_time.second)

            # Next occurrence is tomorrow at scheduled time (UTC)
            next_date = (now + timedelta(days=1)).date()
            next_time_utc = datetime.combine(next_date, schedule_time_utc)

            # Convert back to Bangkok time for display
            next_time_bangkok = next_time_utc + timedelta(hours=BANGKOK_OFFSET_HOURS)
            return next_time_bangkok.strftime('%Y-%m-%d %H:%M:%S')

        elif frequency == 'weekly':
            schedule_day = settings.get('schedule_day')
            schedule_time = settings.get('schedule_time')

            if schedule_day is None or not schedule_time:
                return "Schedule not configured"

            # Convert to datetime.time if string (this is Bangkok time from DB)
            if isinstance(schedule_time, str):
                hour, minute, second = schedule_time.split(':')
                schedule_time = datetime_time(int(hour), int(minute), int(second))

            # Convert to UTC for calculation
            schedule_hour_utc = (schedule_time.hour - BANGKOK_OFFSET_HOURS) % 24
            schedule_time_utc = datetime_time(schedule_hour_utc, schedule_time.minute, schedule_time.second)

            # Find next occurrence of scheduled day
            days_ahead = schedule_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_date = now.date() + timedelta(days=days_ahead)
            next_time_utc = datetime.combine(next_date, schedule_time_utc)

            # Convert back to Bangkok time for display
            next_time_bangkok = next_time_utc + timedelta(hours=BANGKOK_OFFSET_HOURS)
            return next_time_bangkok.strftime('%Y-%m-%d %H:%M:%S')

        return "Unknown"

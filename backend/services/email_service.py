"""
Email Service for Price Change Alerts

This service handles sending HTML emails with price change notifications.
Uses SMTP for email delivery.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending price alert emails via SMTP"""

    def __init__(self):
        """Initialize email service with SMTP configuration from environment"""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'PriceHawk Alerts')
        self.from_email = self.smtp_user

        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending will fail.")

    def send_price_alert_email(
        self,
        to_emails: List[str],
        products: List[Dict],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, any]:
        """
        Send price change alert email to multiple recipients

        Args:
            to_emails: List of recipient email addresses
            products: List of product dictionaries with price change info
            period_start: Start timestamp of detection period
            period_end: End timestamp of detection period

        Returns:
            Dict with 'success' (bool), 'sent_count' (int), 'failed' (list of emails)
        """
        if not products:
            logger.info("No products to send in alert email")
            return {'success': True, 'sent_count': 0, 'failed': []}

        if not to_emails:
            logger.warning("No recipient emails provided")
            return {'success': False, 'sent_count': 0, 'failed': []}

        # Build email content
        subject = f"Price Alert: {len(products)} Products Changed"
        html_body = self._build_html_email(products, period_start, period_end)
        plain_body = self._build_plain_text_email(products, period_start, period_end)

        # Send to each recipient
        sent_count = 0
        failed = []

        for to_email in to_emails:
            try:
                self._send_email(to_email, subject, html_body, plain_body)
                sent_count += 1
                logger.info(f"Alert email sent successfully to {to_email}")
            except Exception as e:
                logger.error(f"Failed to send alert email to {to_email}: {e}")
                failed.append(to_email)

        success = sent_count == len(to_emails)
        return {
            'success': success,
            'sent_count': sent_count,
            'failed': failed
        }

    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify SMTP configuration

        Args:
            to_email: Recipient email address

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "PriceHawk Test Email"
        html_body = self._build_test_html()
        plain_body = "This is a test email from PriceHawk Alert System.\n\nIf you received this, your email configuration is working correctly!"

        try:
            self._send_email(to_email, subject, html_body, plain_body)
            logger.info(f"Test email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send test email to {to_email}: {e}")
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str
    ) -> None:
        """
        Internal method to send email via SMTP

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML version of email
            plain_body: Plain text version of email

        Raises:
            Exception if email sending fails
        """
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach both plain text and HTML versions
        part1 = MIMEText(plain_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        # Send via SMTP
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def _build_html_email(
        self,
        products: List[Dict],
        period_start: datetime,
        period_end: datetime
    ) -> str:
        """Build HTML email body with product table"""

        # Format dates
        start_str = period_start.strftime('%B %d, %Y at %H:%M')
        end_str = period_end.strftime('%B %d, %Y at %H:%M')

        # Limit to top 100 products (sorted by price change percentage)
        limited_products = self._limit_and_sort_products(products)
        more_count = len(products) - len(limited_products) if len(products) > 100 else 0

        # Build product rows
        product_rows = ""
        for product in limited_products:
            product_rows += self._build_product_row(product)

        # More products footer
        more_footer = ""
        if more_count > 0:
            more_footer = f"""
            <tr>
                <td colspan="3" style="padding: 20px; text-align: center; background-color: #f3f4f6; font-style: italic;">
                    ... and {more_count} more products
                </td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Price Change Alert</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f3f4f6;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 20px 0;">
                        <table role="presentation" style="width: 100%; max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #06b6d4; padding: 30px 20px; text-align: center;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                        🔔 Price Change Alert
                                    </h1>
                                    <p style="margin: 10px 0 0; color: #ffffff; font-size: 16px;">
                                        {len(products)} products have changed price
                                    </p>
                                </td>
                            </tr>

                            <!-- Period Info -->
                            <tr>
                                <td style="padding: 20px; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb;">
                                    <p style="margin: 0; font-size: 14px; color: #6b7280;">
                                        <strong>Period:</strong> {start_str} → {end_str}
                                    </p>
                                </td>
                            </tr>

                            <!-- Products Table -->
                            {product_rows}
                            {more_footer}

                            <!-- Footer -->
                            <tr>
                                <td style="padding: 30px 20px; text-align: center; background-color: #f9fafb; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0 0 10px; font-size: 14px; color: #6b7280;">
                                        View all products and detailed price history on your dashboard
                                    </p>
                                    <a href="#" style="display: inline-block; padding: 12px 24px; background-color: #06b6d4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold;">
                                        Go to Dashboard
                                    </a>
                                    <p style="margin: 20px 0 0; font-size: 12px; color: #9ca3af;">
                                        This is an automated alert from PriceHawk
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return html

    def _build_product_row(self, product: Dict) -> str:
        """Build HTML table row for a single product"""
        # Extract product info
        name = product.get('name', 'Unknown Product')
        category = product.get('category', '')
        brand = product.get('brand', '')
        retailer = product.get('retailer_name', '')
        old_price = product.get('old_price', 0)
        new_price = product.get('new_price', 0)
        images = product.get('images', [])

        # Get first image or placeholder
        image_url = images[0] if images and len(images) > 0 else 'https://via.placeholder.com/80'

        # Calculate price change
        price_diff = new_price - old_price
        price_change_pct = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0

        # Determine if price went up or down
        if price_diff > 0:
            change_color = "#ef4444"  # red
            change_arrow = "↑"
            change_text = f"+{price_change_pct:.1f}%"
        elif price_diff < 0:
            change_color = "#10b981"  # green
            change_arrow = "↓"
            change_text = f"{price_change_pct:.1f}%"
        else:
            change_color = "#6b7280"  # gray
            change_arrow = "="
            change_text = "0%"

        # Build product info text
        info_parts = []
        if brand:
            info_parts.append(f"<strong>{brand}</strong>")
        if category:
            info_parts.append(category)
        if retailer:
            info_parts.append(retailer)
        info_text = " • ".join(info_parts)

        row = f"""
        <tr>
            <td style="padding: 20px; border-bottom: 1px solid #e5e7eb;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 80px; vertical-align: top;">
                            <img src="{image_url}" alt="{name}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
                        </td>
                        <td style="padding-left: 15px; vertical-align: top;">
                            <p style="margin: 0 0 8px; font-size: 16px; font-weight: bold; color: #111827;">
                                {name}
                            </p>
                            <p style="margin: 0; font-size: 14px; color: #6b7280;">
                                {info_text}
                            </p>
                        </td>
                        <td style="width: 200px; text-align: right; vertical-align: top; padding-left: 20px;">
                            <p style="margin: 0 0 4px; font-size: 12px; color: #9ca3af; text-decoration: line-through;">
                                ฿{old_price:,.2f}
                            </p>
                            <p style="margin: 0 0 4px; font-size: 20px; font-weight: bold; color: #111827;">
                                ฿{new_price:,.2f}
                            </p>
                            <p style="margin: 0; font-size: 14px; font-weight: bold; color: {change_color};">
                                {change_arrow} {change_text}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

        return row

    def _build_plain_text_email(
        self,
        products: List[Dict],
        period_start: datetime,
        period_end: datetime
    ) -> str:
        """Build plain text email body as fallback"""
        start_str = period_start.strftime('%B %d, %Y at %H:%M')
        end_str = period_end.strftime('%B %d, %Y at %H:%M')

        limited_products = self._limit_and_sort_products(products)
        more_count = len(products) - len(limited_products) if len(products) > 100 else 0

        text = f"""
PRICE CHANGE ALERT
==================

{len(products)} products have changed price

Period: {start_str} → {end_str}

PRODUCTS:
---------

"""

        for i, product in enumerate(limited_products, 1):
            name = product.get('name', 'Unknown Product')
            brand = product.get('brand', '')
            category = product.get('category', '')
            old_price = product.get('old_price', 0)
            new_price = product.get('new_price', 0)

            price_diff = new_price - old_price
            change_symbol = "↑" if price_diff > 0 else "↓" if price_diff < 0 else "="

            text += f"{i}. {name}\n"
            if brand:
                text += f"   Brand: {brand}\n"
            if category:
                text += f"   Category: {category}\n"
            text += f"   Price: ฿{old_price:,.2f} → ฿{new_price:,.2f} {change_symbol}\n\n"

        if more_count > 0:
            text += f"... and {more_count} more products\n\n"

        text += """
--
This is an automated alert from PriceHawk
View all products on your dashboard
"""

        return text

    def _build_test_html(self) -> str:
        """Build HTML for test email"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Test Email</title>
        </head>
        <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h1 style="color: #06b6d4; margin: 0 0 20px;">✅ Email Configuration Working!</h1>
                <p style="font-size: 16px; color: #374151; line-height: 1.6; margin: 0 0 20px;">
                    This is a test email from <strong>PriceHawk Alert System</strong>.
                </p>
                <p style="font-size: 16px; color: #374151; line-height: 1.6; margin: 0 0 20px;">
                    If you received this email, your SMTP configuration is set up correctly and price change alerts will be delivered successfully.
                </p>
                <div style="background-color: #f9fafb; padding: 20px; border-radius: 6px; border-left: 4px solid #06b6d4;">
                    <p style="margin: 0; font-size: 14px; color: #6b7280;">
                        <strong>Next steps:</strong><br>
                        1. Add email addresses to your alert list<br>
                        2. Configure your preferred alert schedule<br>
                        3. Enable alerts in the settings
                    </p>
                </div>
                <p style="margin: 30px 0 0; font-size: 12px; color: #9ca3af; text-align: center;">
                    PriceHawk - Price Monitoring System
                </p>
            </div>
        </body>
        </html>
        """
        return html

    def _limit_and_sort_products(self, products: List[Dict], limit: int = 100) -> List[Dict]:
        """
        Sort products by price drop percentage and limit to top N

        Args:
            products: List of product dictionaries
            limit: Maximum number of products to return

        Returns:
            Limited and sorted list of products
        """
        # Calculate price change percentage for each product
        for product in products:
            old_price = product.get('old_price', 0)
            new_price = product.get('new_price', 0)
            if old_price > 0:
                change_pct = ((new_price - old_price) / old_price) * 100
                product['_change_pct'] = change_pct
            else:
                product['_change_pct'] = 0

        # Sort by change percentage (biggest drops first, then biggest increases)
        sorted_products = sorted(products, key=lambda p: p.get('_change_pct', 0))

        # Return top N
        return sorted_products[:limit]

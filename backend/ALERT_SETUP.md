# Price Change Alert System Setup

This document describes the price change alert system that sends email notifications when product prices change.

## Overview

The alert system monitors all products for price changes and sends email notifications according to a configurable schedule. Users can manage alert settings and email recipients through the web interface.

## Architecture

### Components

1. **Database Tables** (`database/init/06_price_alerts.sql`)
   - `price_alert_settings` - Global alert configuration (single row)
   - `price_alert_emails` - Email recipient list
   - `price_alert_history` - Log of sent alerts

2. **Backend Services**
   - `services/email_service.py` - Email sending via SMTP
   - `services/alert_service.py` - Alert logic and scheduling
   - `alert_checker.py` - Cron job entry point

3. **API Endpoints** (`main.py`)
   - `GET /api/price-alerts/settings` - Get alert configuration
   - `PUT /api/price-alerts/settings` - Update alert configuration
   - `GET /api/price-alerts/emails` - List email recipients
   - `POST /api/price-alerts/emails` - Add email recipient
   - `DELETE /api/price-alerts/emails/{email_id}` - Remove email recipient
   - `GET /api/price-alerts/history` - Get alert send history
   - `POST /api/price-alerts/test` - Send test email

4. **Frontend**
   - `/price-change` - Settings page for managing alerts

## Setup Instructions

### 1. Database Migration

Run the database migration to create the required tables:

```bash
psql $DATABASE_URL < database/init/06_price_alerts.sql
```

This will create:
- `price_alert_settings` table with default settings (daily at 9 AM, enabled)
- `price_alert_emails` table (empty)
- `price_alert_history` table (empty)

### 2. SMTP Configuration

Configure email settings by adding environment variables:

**For Gmail:**

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated password

3. Add environment variables:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # 16-character app password from step 2
SMTP_FROM_NAME=PriceHawk Alerts
```

**For other SMTP providers:**

```bash
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM_NAME=PriceHawk Alerts
```

**Popular SMTP providers:**
- **SendGrid**: smtp.sendgrid.net (port 587)
- **AWS SES**: email-smtp.us-east-1.amazonaws.com (port 587)
- **Mailgun**: smtp.mailgun.org (port 587)
- **Outlook**: smtp-mail.outlook.com (port 587)

### 3. Railway Cron Job Setup

Add a new cron service to Railway:

1. Go to your Railway project
2. Navigate to the service settings
3. Click on "Cron"
4. Add new cron job:

```
Schedule: 0 * * * *
Command: python backend/alert_checker.py
```

This runs the alert checker every hour on the hour.

**Alternative schedules:**
- Every 30 minutes: `*/30 * * * *`
- Every 2 hours: `0 */2 * * *`
- Daily at 9 AM: `0 9 * * *`

### 4. Test the System

1. **Configure settings via UI:**
   - Navigate to `/price-change` in the web app
   - Add your email address to the recipient list
   - Set schedule to "Immediate" for testing
   - Enable alerts

2. **Send test email:**
   - Click "Send Test Email" button
   - Check your inbox (and spam folder)
   - Verify email formatting looks correct

3. **Manual test with real data:**
   ```bash
   python backend/alert_checker.py
   ```

4. **Check logs:**
   ```bash
   # View Railway logs
   railway logs

   # Or check alert history via API
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://your-app.railway.app/api/price-alerts/history
   ```

## Configuration Options

### Alert Schedules

| Frequency | Description | Example |
|-----------|-------------|---------|
| Immediate | Send within 1 minute of price change | Real-time alerts (with 1min debounce) |
| Hourly | Send once per hour if changes exist | Every hour on the hour |
| Daily | Send once per day at specific time | Every day at 9:00 AM |
| Weekly | Send once per week on specific day | Every Monday at 9:00 AM |

### Schedule Logic

The cron job runs **hourly**, but the alert service checks internally if it should actually send based on the configured schedule:

- **Immediate**: Sends if at least 1 minute has passed since last alert
- **Hourly**: Sends if at least 1 hour has passed
- **Daily**: Sends if current time is past scheduled time AND we haven't sent today
- **Weekly**: Sends if today is the scheduled day AND current time is past scheduled time AND we haven't sent this week

This design allows flexibility without creating multiple cron jobs.

## Email Content

Emails include:

- **Header**: "Price Change Alert" with product count
- **Period**: Date/time range of price changes
- **Product List**: Up to 100 products (sorted by biggest price drops first)
  - Product image (80x80px)
  - Product name, brand, category, retailer
  - Old price → New price
  - Percentage change with color coding (green for drops, red for increases)
- **Footer**: Link to dashboard
- **Plain text fallback**: For email clients that don't support HTML

If more than 100 products changed, the email shows "... and X more products" at the bottom.

## Monitoring

### Check Alert Status

Via web UI:
- Navigate to `/price-change`
- View "Alert Status" section showing:
  - Last alert sent timestamp
  - Next scheduled alert
  - Number of recipients
  - Current enabled status

Via API:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-app.railway.app/api/price-alerts/settings
```

### View Alert History

Via API:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-app.railway.app/api/price-alerts/history?limit=50
```

### Check Cron Job Logs

```bash
railway logs --filter="alert_checker"
```

Look for:
- "Alert check completed" - successful run
- "Products with changes: X" - number of products that changed
- "Alerts sent: X" - number of emails sent
- Any error messages

## Troubleshooting

### Emails Not Sending

1. **Check SMTP configuration:**
   ```bash
   # Test email via UI
   # Click "Send Test Email" button
   ```

2. **Verify environment variables:**
   ```bash
   railway variables
   ```

3. **Check for SMTP errors in logs:**
   ```bash
   railway logs | grep -i smtp
   ```

4. **Common issues:**
   - Gmail: App password not generated or 2FA not enabled
   - Firewall: Port 587 blocked
   - Invalid credentials: Wrong username/password
   - Rate limiting: Too many emails sent too quickly

### No Alerts Being Sent

1. **Check if alerts are enabled:**
   - Go to `/price-change`
   - Verify "Enable price change alerts" is checked

2. **Check if email recipients exist:**
   - At least one email must be added

3. **Check if price changes occurred:**
   ```bash
   # Check recent price history
   psql $DATABASE_URL -c "
     SELECT COUNT(*) FROM price_history
     WHERE scraped_at > NOW() - INTERVAL '24 hours'
   "
   ```

4. **Check schedule logic:**
   - If frequency is "daily" and it's 8 AM but schedule is 9 AM, no alert will be sent yet
   - Review "Next alert" time in status section

### Emails Going to Spam

1. **Use reputable SMTP service:**
   - Gmail, SendGrid, AWS SES are good options
   - Avoid using free/suspicious domains

2. **Add SPF/DKIM records:**
   - Configure your domain's DNS settings
   - Consult your SMTP provider's documentation

3. **Keep email content clean:**
   - No promotional language
   - No misleading subject lines
   - Include plain text version

## Performance Considerations

### Large Price Change Volumes

If thousands of products change price daily:

1. **Email is limited to top 100 products** (sorted by biggest price drop)
2. **Consider increasing limit** in `email_service.py`:
   ```python
   limited_products = self._limit_and_sort_products(products, limit=200)
   ```

3. **Or implement pagination:**
   - Send multiple emails: "Page 1 of 5", "Page 2 of 5", etc.
   - Add delay between emails to avoid rate limiting

### Database Performance

The price change query joins `price_history` with `products` and `retailers`:

```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT ...
FROM price_history ph
WHERE ph.scraped_at >= $1;
```

If slow:
1. **Ensure index exists:**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at
   ON price_history(scraped_at DESC);
   ```

2. **Limit search window:**
   - Only check last 7 days instead of all history
   - Archive old price_history data

## Security

### Email Address Validation

- Email format validated via regex
- Duplicate emails prevented via UNIQUE constraint
- Email verification field exists for future implementation

### API Authentication

All endpoints require authentication via `get_current_user` dependency.

### SMTP Credentials

- Stored as environment variables (not in code)
- Use app passwords (not account passwords) for Gmail
- Rotate credentials periodically

## Future Enhancements

Potential improvements (not currently implemented):

1. **Email verification flow**
   - Send confirmation link to new email addresses
   - Mark as verified only after clicking link

2. **Alert threshold filters**
   - Only alert when price drops >10%
   - Only alert when price is below specific amount

3. **Watchlist-specific alerts**
   - Alert only for products in specific watchlist groups
   - Different schedules for different groups

4. **Unsubscribe links**
   - One-click unsubscribe in email footer
   - Comply with email marketing regulations

5. **Rich email templates**
   - Price history charts
   - Trend indicators
   - Summary statistics

6. **SMS/Push notifications**
   - Alternative to email
   - Real-time mobile alerts

7. **Per-user settings**
   - Different schedules for different users
   - User-specific email preferences

## Maintenance

### Regular Tasks

1. **Monitor alert history:**
   - Check for failed sends
   - Verify products are being detected correctly

2. **Clean up old history:**
   ```sql
   -- Keep only last 90 days of alert history
   DELETE FROM price_alert_history
   WHERE sent_at < NOW() - INTERVAL '90 days';
   ```

3. **Verify email list:**
   - Remove bounced emails
   - Update changed addresses

### Updating Configuration

To change default settings:

```sql
UPDATE price_alert_settings SET
  schedule_frequency = 'daily',
  schedule_time = '08:00:00',
  enabled = true
WHERE setting_id = 1;
```

## Support

For issues or questions:

1. Check Railway logs: `railway logs`
2. Review API responses for error details
3. Test SMTP configuration with test email button
4. Verify database tables exist and have data

## Related Documentation

- [CRON_SETUP.md](./CRON_SETUP.md) - Price updater cron job
- [Database Schema](../database/init/06_price_alerts.sql)
- [Email Service](./services/email_service.py)
- [Alert Service](./services/alert_service.py)

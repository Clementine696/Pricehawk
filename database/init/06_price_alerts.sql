-- Price Alert System Schema
-- This schema supports a global price change notification system

-- Alert schedule and configuration (single row table)
CREATE TABLE IF NOT EXISTS price_alert_settings (
    setting_id SERIAL PRIMARY KEY,
    schedule_frequency VARCHAR(20) NOT NULL CHECK (schedule_frequency IN ('immediate', 'hourly', 'daily', 'weekly')),
    schedule_time TIME DEFAULT '09:00:00',  -- For daily/weekly schedules
    schedule_day INTEGER CHECK (schedule_day >= 0 AND schedule_day <= 6),  -- 0=Monday, 6=Sunday (for weekly)
    enabled BOOLEAN DEFAULT TRUE,
    last_alert_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ensure only one settings row can exist
CREATE UNIQUE INDEX IF NOT EXISTS idx_price_alert_settings_single_row
ON price_alert_settings ((setting_id IS NOT NULL));

-- Email addresses for alert recipients
CREATE TABLE IF NOT EXISTS price_alert_emails (
    email_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast email lookups
CREATE INDEX IF NOT EXISTS idx_alert_emails ON price_alert_emails(email);

-- Alert send history log
CREATE TABLE IF NOT EXISTS price_alert_history (
    alert_id SERIAL PRIMARY KEY,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    products_count INTEGER NOT NULL,
    emails_sent TEXT[] NOT NULL,  -- Array of email addresses
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    error_message TEXT,
    period_start TIMESTAMP NOT NULL,  -- Start of price change detection period
    period_end TIMESTAMP NOT NULL     -- End of price change detection period
);

-- Create index for history queries
CREATE INDEX IF NOT EXISTS idx_alert_history_sent_at ON price_alert_history(sent_at DESC);

-- Insert default settings (only if table is empty)
INSERT INTO price_alert_settings (schedule_frequency, schedule_time, enabled)
SELECT 'daily', '09:00:00', TRUE
WHERE NOT EXISTS (SELECT 1 FROM price_alert_settings LIMIT 1);

-- Comments for documentation
COMMENT ON TABLE price_alert_settings IS 'Global settings for price change alerts (single row)';
COMMENT ON COLUMN price_alert_settings.schedule_frequency IS 'Alert frequency: immediate, hourly, daily, or weekly';
COMMENT ON COLUMN price_alert_settings.schedule_time IS 'Time of day for daily/weekly alerts (HH:MM:SS)';
COMMENT ON COLUMN price_alert_settings.schedule_day IS 'Day of week for weekly alerts (0=Monday, 6=Sunday)';
COMMENT ON COLUMN price_alert_settings.last_alert_sent_at IS 'Timestamp of last alert sent (used to detect price changes)';

COMMENT ON TABLE price_alert_emails IS 'Email addresses to receive price change alerts';
COMMENT ON COLUMN price_alert_emails.verified IS 'Email verification status (for future verification flow)';

COMMENT ON TABLE price_alert_history IS 'Log of all alert emails sent';
COMMENT ON COLUMN price_alert_history.products_count IS 'Number of products with price changes in this alert';
COMMENT ON COLUMN price_alert_history.emails_sent IS 'Array of recipient emails for this alert';
COMMENT ON COLUMN price_alert_history.status IS 'success=all sent, failed=none sent, partial=some failed';
COMMENT ON COLUMN price_alert_history.period_start IS 'Start timestamp for price change detection period';
COMMENT ON COLUMN price_alert_history.period_end IS 'End timestamp for price change detection period';

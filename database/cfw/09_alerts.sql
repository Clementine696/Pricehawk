-- Migration: Price Change Alerts
-- Same schema as TWD system for full compatibility with alert_service.py

CREATE TABLE IF NOT EXISTS price_alert_settings (
    setting_id SERIAL PRIMARY KEY,
    schedule_frequency VARCHAR(20) NOT NULL CHECK (schedule_frequency IN ('immediate', 'hourly', 'daily', 'weekly')),
    schedule_time TIME DEFAULT '09:00:00',
    schedule_day INTEGER CHECK (schedule_day >= 0 AND schedule_day <= 6),
    enabled BOOLEAN DEFAULT TRUE,
    last_alert_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_price_alert_settings_single_row
ON price_alert_settings ((setting_id IS NOT NULL));

CREATE TABLE IF NOT EXISTS price_alert_emails (
    email_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_emails ON price_alert_emails(email);

CREATE TABLE IF NOT EXISTS price_alert_history (
    alert_id SERIAL PRIMARY KEY,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    products_count INTEGER NOT NULL,
    emails_sent TEXT[] NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    error_message TEXT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alert_history_sent_at ON price_alert_history(sent_at DESC);

INSERT INTO price_alert_settings (schedule_frequency, schedule_time, enabled)
SELECT 'daily', '09:00:00', TRUE
WHERE NOT EXISTS (SELECT 1 FROM price_alert_settings LIMIT 1);

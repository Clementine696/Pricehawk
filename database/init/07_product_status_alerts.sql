-- Product Status Alert Tracking
-- This migration adds a column to track product availability status for alerting

-- Add last_alert_status column to products table
-- This tracks what status was last alerted to users
-- Values: 'active', 'inactive'
ALTER TABLE products ADD COLUMN IF NOT EXISTS last_alert_status VARCHAR(20)
	DEFAULT 'active'
	CHECK (last_alert_status IN ('active', 'inactive'));

-- Backfill existing rows to active (only when column was just added)
UPDATE products
SET last_alert_status = 'active'
WHERE last_alert_status IS NULL;

-- Create index for efficient status change queries
CREATE INDEX IF NOT EXISTS idx_products_alert_status ON products(last_alert_status, scrape_fail_count);

-- Add comment for clarity
COMMENT ON COLUMN products.last_alert_status IS 'Tracks the last alerted product status. NULL = never alerted, active = last alerted as active, inactive = last alerted as inactive. Used with scrape_fail_count to detect status changes.';

-- Logic for status change detection:
-- 1. Product becomes INACTIVE: last_alert_status = 'active' AND scrape_fail_count >= 3
-- 2. Product becomes ACTIVE: last_alert_status = 'inactive' AND scrape_fail_count < 3
-- 3. After sending alert, update last_alert_status to the new status

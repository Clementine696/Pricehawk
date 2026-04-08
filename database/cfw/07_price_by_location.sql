-- Migration: Price by Location (Makro branch pricing)
-- Tracks Makro prices per branch for products in selected watchlists

-- ============================================================================
-- 1. Makro Locations (branches)
-- ============================================================================
CREATE TABLE IF NOT EXISTS makro_locations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    branch_code TEXT UNIQUE NOT NULL,
    region TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- 2. Monitored Config (which watchlists + which locations to scrape)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pbl_monitored_watchlists (
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    PRIMARY KEY (watchlist_id)
);

CREATE TABLE IF NOT EXISTS pbl_monitored_locations (
    location_id INTEGER NOT NULL REFERENCES makro_locations(id) ON DELETE CASCADE,
    PRIMARY KEY (location_id)
);

-- ============================================================================
-- 3. Location Prices (scraped Makro price per product per branch)
-- ============================================================================
CREATE TABLE IF NOT EXISTS makro_location_prices (
    id SERIAL PRIMARY KEY,
    makro_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES makro_locations(id) ON DELETE CASCADE,
    price DECIMAL(10, 2),
    scraped_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (makro_product_id, location_id)
);

CREATE INDEX IF NOT EXISTS idx_makro_location_prices_product ON makro_location_prices(makro_product_id);
CREATE INDEX IF NOT EXISTS idx_makro_location_prices_location ON makro_location_prices(location_id);

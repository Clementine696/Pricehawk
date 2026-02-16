-- Location-based Price Tracking
-- Support for tracking prices across different store locations (GlobalHouse initially)

-- 1. Locations table - Store location information
CREATE TABLE IF NOT EXISTS locations (
    location_id SERIAL PRIMARY KEY,
    retailer_id VARCHAR(10) NOT NULL REFERENCES retailers(retailer_id),
    name_th VARCHAR(100) NOT NULL,           -- Thai name: "นครปฐม"
    name_en VARCHAR(100),                     -- English name: "Nakhon Pathom"
    url_param VARCHAR(100),                   -- URL parameter for scraper
    branch_code VARCHAR(50),                  -- Branch code: "GH-123"
    branch_name VARCHAR(200),                 -- Full branch name: "สาขานครปฐม"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(retailer_id, branch_code)
);

-- 2. Monitored Groups - Track which S-depts to monitor for location pricing
CREATE TABLE IF NOT EXISTS location_monitored_groups (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES watchlist_sku_groups(group_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id)
);

-- 3. Monitored Locations - Track which locations to scrape
CREATE TABLE IF NOT EXISTS location_monitored_locations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(location_id)
);

-- 4. Product Location Prices - Current price per product per location
CREATE TABLE IF NOT EXISTS product_location_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
    price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'THB',
    last_updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, location_id)
);

-- 5. Location Price History - Track price changes over time
CREATE TABLE IF NOT EXISTS location_price_history (
    history_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'THB',
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_locations_retailer ON locations(retailer_id);
CREATE INDEX IF NOT EXISTS idx_locations_active ON locations(is_active);
CREATE INDEX IF NOT EXISTS idx_product_location_prices_product ON product_location_prices(product_id);
CREATE INDEX IF NOT EXISTS idx_product_location_prices_location ON product_location_prices(location_id);
CREATE INDEX IF NOT EXISTS idx_location_price_history_product ON location_price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_location_price_history_location ON location_price_history(location_id);
CREATE INDEX IF NOT EXISTS idx_location_price_history_date ON location_price_history(scraped_at);

-- Initial schema setup for PriceHawk
-- This runs automatically when the container is first created

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Retailers table (using string codes as ID)
-- Codes: twd=Thai Watsadu, hp=HomePro, dh=Do Home, btv=Boonthavorn, gbh=Global House
CREATE TABLE IF NOT EXISTS retailers (
    retailer_id VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT UNIQUE,
    logo_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    retailer_id VARCHAR(10) NOT NULL REFERENCES retailers(retailer_id),
    sku TEXT NOT NULL,
    name TEXT,
    brand TEXT,
    category TEXT,
    link TEXT NOT NULL,
    image TEXT,
    description TEXT,
    current_price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    lowest_price DECIMAL(10, 2),
    highest_price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'THB',
    last_updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT products_retailer_sku_unique UNIQUE (retailer_id, sku)
);

-- 4. Product Matches table
CREATE TABLE IF NOT EXISTS product_matches (
    match_id SERIAL PRIMARY KEY,
    base_product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    candidate_product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    retailer_id VARCHAR(10) NOT NULL REFERENCES retailers(retailer_id),

    is_same BOOLEAN,
    confidence_score NUMERIC(5,4),
    reason TEXT,
    match_type TEXT DEFAULT 'auto',

    verified_by_user BOOLEAN DEFAULT FALSE,
    verified_result BOOLEAN,
    verified_at TIMESTAMP,
    verified_user_id INTEGER REFERENCES users(user_id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_match_pair UNIQUE (base_product_id, candidate_product_id)
);

-- 5. Price History table
CREATE TABLE IF NOT EXISTS price_history (
    price_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'THB',
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_retailer ON products(retailer_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(scraped_at);
CREATE INDEX IF NOT EXISTS idx_product_matches_base ON product_matches(base_product_id);
CREATE INDEX IF NOT EXISTS idx_product_matches_candidate ON product_matches(candidate_product_id);

-- Auto-update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_matches_updated_at
    BEFORE UPDATE ON product_matches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default retailers
INSERT INTO retailers (retailer_id, name, domain) VALUES
    ('twd', 'Thai Watsadu', 'thaiwatsadu.com'),
    ('hp', 'HomePro', 'homepro.co.th'),
    ('mgh', 'MegaHome', 'megahome.co.th'),
    ('dh', 'Do Home', 'dohome.co.th'),
    ('btv', 'Boonthavorn', 'boonthavorn.com'),
    ('gbh', 'Global House', 'globalhouse.co.th')
ON CONFLICT (retailer_id) DO NOTHING;

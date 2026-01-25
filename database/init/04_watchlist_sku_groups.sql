-- Watchlist SKU Groups
-- Similar to category-based watchlist groups, but for individual SKUs

CREATE TABLE IF NOT EXISTS watchlist_sku_groups (
    group_id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist_sku_group_products (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES watchlist_sku_groups(group_id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, sku)
);

CREATE INDEX idx_watchlist_sku_group_products_group ON watchlist_sku_group_products(group_id);
CREATE INDEX idx_watchlist_sku_group_products_sku ON watchlist_sku_group_products(sku);

-- Insert some default SKU-based watchlist groups
INSERT INTO watchlist_sku_groups (name) VALUES
('My Favorites'),
('Price Drop Alerts'),
('Hot Deals')
ON CONFLICT (name) DO NOTHING;

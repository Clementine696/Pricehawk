-- Migration: Global Watchlist Groups (Category Groups)
-- Changes watchlist from user-specific to global category groups

-- Watchlist Groups table (global, not user-specific)
CREATE TABLE IF NOT EXISTS watchlist_groups (
    group_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,  -- e.g., 'glue_and_cement', 'paint_supplies'
    display_name TEXT NOT NULL,  -- e.g., 'Glue & Cement', 'Paint Supplies'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Categories in each watchlist group
CREATE TABLE IF NOT EXISTS watchlist_group_categories (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES watchlist_groups(group_id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    
    -- Each category can only be in a group once
    CONSTRAINT unique_group_category UNIQUE (group_id, category)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_watchlist_group_categories_group ON watchlist_group_categories(group_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_group_categories_category ON watchlist_group_categories(category);

-- Insert some default watchlist groups
INSERT INTO watchlist_groups (name, display_name, description) VALUES
    ('glue_and_cement', 'Glue & Cement', 'Adhesives, glues, and cement products'),
    ('paint_supplies', 'Paint Supplies', 'Paints, brushes, and painting accessories'),
    ('tools_and_hardware', 'Tools & Hardware', 'Hand tools, power tools, and hardware'),
    ('building_materials', 'Building Materials', 'Construction and building materials')
ON CONFLICT (name) DO NOTHING;

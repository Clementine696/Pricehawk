-- ============================================================================
-- Product Matches Table
-- ============================================================================
-- This table stores matched relationships between CFW and Makro products
-- One CFW product can have multiple Makro matches (e.g., top 5 suggestions)
-- User will verify which match is correct

CREATE TABLE IF NOT EXISTS product_matches (
    match_id SERIAL PRIMARY KEY,
    
    -- Foreign keys to products table
    cfw_product_id INTEGER NOT NULL,
    makro_product_id INTEGER NOT NULL,
    
    -- Match metadata
    match_score DECIMAL(5,2), -- Similarity score (0-100) for ranking suggestions
    
    -- Verification status
    is_verified BOOLEAN DEFAULT FALSE, -- Only ONE match per CFW product should be TRUE
    verified_at TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    FOREIGN KEY (cfw_product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (makro_product_id) REFERENCES products(id) ON DELETE CASCADE,
    
    -- Prevent duplicate pairs (same CFW + Makro combination)
    UNIQUE (cfw_product_id, makro_product_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_product_matches_cfw ON product_matches(cfw_product_id);
CREATE INDEX IF NOT EXISTS idx_product_matches_makro ON product_matches(makro_product_id);
CREATE INDEX IF NOT EXISTS idx_product_matches_verified ON product_matches(is_verified);
CREATE INDEX IF NOT EXISTS idx_product_matches_score ON product_matches(match_score DESC);

-- Partial unique index: Only one verified match per CFW product
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_matches_one_verified 
    ON product_matches(cfw_product_id) 
    WHERE is_verified = TRUE;

-- Comments for documentation
COMMENT ON TABLE product_matches IS 'Stores multiple match suggestions between CFW and Makro products. One CFW product can have multiple matches, but only one can be verified.';
COMMENT ON COLUMN product_matches.match_score IS 'Similarity score (0-100) for ranking match suggestions';
COMMENT ON COLUMN product_matches.is_verified IS 'TRUE for the confirmed match. Only ONE match per CFW product can be verified.';
COMMENT ON COLUMN product_matches.verified_at IS 'Timestamp when match was verified by user';

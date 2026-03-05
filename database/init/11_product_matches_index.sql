-- Performance optimization for product_matches queries
-- Add composite index for verified matches filter

-- Index for filtering verified matches (used in location-watch queries)
CREATE INDEX IF NOT EXISTS idx_product_matches_verified 
ON product_matches(verified_by_user, is_same) 
WHERE verified_by_user = TRUE AND is_same = TRUE;

-- Composite index for common join pattern with verification check
CREATE INDEX IF NOT EXISTS idx_product_matches_base_verified 
ON product_matches(base_product_id, verified_by_user, is_same);

CREATE INDEX IF NOT EXISTS idx_product_matches_candidate_verified 
ON product_matches(candidate_product_id, verified_by_user, is_same);

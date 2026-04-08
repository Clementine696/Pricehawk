-- Migration: Fix verification constraint to allow multiple verified but only one correct match
--
-- OLD behavior: Only one verified match per CFW product (too restrictive)
-- NEW behavior: Multiple verified matches allowed, but only ONE can be correct
--
-- This allows:
-- - Match 1: is_verified=TRUE, is_same=FALSE (rejected)
-- - Match 2: is_verified=TRUE, is_same=FALSE (rejected)
-- - Match 3: is_verified=TRUE, is_same=TRUE  (correct) ✓
--
-- But prevents:
-- - Match 1: is_verified=TRUE, is_same=TRUE  (correct)
-- - Match 2: is_verified=TRUE, is_same=TRUE  (correct) ✗ ERROR

-- Drop the old restrictive index
DROP INDEX IF EXISTS idx_product_matches_one_verified;

-- Create new index: only one verified CORRECT match per CFW product
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_matches_one_correct 
    ON product_matches(cfw_product_id) 
    WHERE is_verified = TRUE AND is_same = TRUE;

-- Update comments for clarity
COMMENT ON TABLE product_matches IS 'Stores multiple match suggestions between CFW and Makro products. Users can verify multiple matches (some as incorrect, one as correct).';
COMMENT ON COLUMN product_matches.is_verified IS 'TRUE when user has reviewed this match. Multiple matches can be verified.';
COMMENT ON COLUMN product_matches.is_same IS 'Result of verification: TRUE = correct match, FALSE = incorrect match, NULL = not yet verified. Only ONE correct match allowed per CFW product.';

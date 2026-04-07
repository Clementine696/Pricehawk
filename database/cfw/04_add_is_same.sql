-- Migration: Add is_same column to product_matches
--
-- is_verified = user has reviewed this match (TRUE/FALSE)
-- is_same     = result of the review: TRUE = correct match, FALSE = rejected, NULL = not yet reviewed

ALTER TABLE product_matches ADD COLUMN IF NOT EXISTS is_same BOOLEAN DEFAULT NULL;

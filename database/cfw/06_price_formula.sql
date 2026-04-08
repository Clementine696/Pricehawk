-- Migration: Add price_formula to product_matches
-- Formula adjusts Makro price to be comparable to CFW unit price
-- e.g. Makro sells 5-pack: formula = '/5' → adjusted_makro = makro_price / 5
-- e.g. Makro sells per kg, CFW per 500g: formula = '*0.5'

ALTER TABLE product_matches ADD COLUMN IF NOT EXISTS price_formula TEXT DEFAULT NULL;

COMMENT ON COLUMN product_matches.price_formula IS
  'Formula to adjust Makro price to CFW unit. Stored as multiplier/divisor e.g. *5, /2, *5/2. NULL = no adjustment.';

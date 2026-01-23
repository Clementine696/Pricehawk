-- Fix PostgreSQL sequences after data migration
-- Run this script after importing data to reset all sequences to the correct values

-- Fix users table sequence
SELECT setval('users_user_id_seq', (SELECT COALESCE(MAX(user_id), 1) FROM users), true);

-- Fix products table sequence
SELECT setval('products_product_id_seq', (SELECT COALESCE(MAX(product_id), 1) FROM products), true);

-- Fix product_matches table sequence
SELECT setval('product_matches_match_id_seq', (SELECT COALESCE(MAX(match_id), 1) FROM product_matches), true);

-- Fix price_history table sequence
SELECT setval('price_history_price_id_seq', (SELECT COALESCE(MAX(price_id), 1) FROM price_history), true);

-- Verify sequences are correct
SELECT 'users_user_id_seq' as sequence_name, last_value FROM users_user_id_seq
UNION ALL
SELECT 'products_product_id_seq', last_value FROM products_product_id_seq
UNION ALL
SELECT 'product_matches_match_id_seq', last_value FROM product_matches_match_id_seq
UNION ALL
SELECT 'price_history_price_id_seq', last_value FROM price_history_price_id_seq;

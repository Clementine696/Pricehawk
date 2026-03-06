-- Migration: Add extraction_pattern column to price_history
-- Date: 2026-03-06
-- Purpose: Track which extraction method was used for each price update

ALTER TABLE price_history 
ADD COLUMN extraction_pattern VARCHAR(100);

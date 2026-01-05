-- Migration: Add user category watchlist
-- Run this after 01_schema.sql

-- User Category Watchlist table
-- Allows users to watch specific categories for price changes
CREATE TABLE IF NOT EXISTS user_category_watchlist (
    watchlist_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Each user can only watch a category once
    CONSTRAINT unique_user_category UNIQUE (user_id, category)
);

-- Index for faster lookups by user
CREATE INDEX IF NOT EXISTS idx_user_category_watchlist_user ON user_category_watchlist(user_id);

-- Index for faster lookups by category
CREATE INDEX IF NOT EXISTS idx_user_category_watchlist_category ON user_category_watchlist(category);

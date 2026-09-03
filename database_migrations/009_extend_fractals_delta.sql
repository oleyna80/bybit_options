-- ============================================================================
-- Migration: 009_extend_fractals_delta.sql
-- Description: Add Delta enrichment columns to fractals_cache
-- Author: Roo
-- Date: 2026-01-20
-- ============================================================================

-- Add Delta enrichment columns to fractals_cache
ALTER TABLE fractals_cache
ADD COLUMN IF NOT EXISTS delta_1h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS delta_4h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS delta_24h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS oi_delta_24h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS orderbook_imbalance NUMERIC(5, 4),
ADD COLUMN IF NOT EXISTS confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMPTZ;

-- Index for finding unenriched fractals
CREATE INDEX IF NOT EXISTS idx_fractals_unenriched
ON fractals_cache (is_key_fractal, enriched_at)
WHERE is_key_fractal = true AND enriched_at IS NULL;

-- Comments
COMMENT ON COLUMN fractals_cache.delta_1h IS 'Filtered delta over 1 hour';
COMMENT ON COLUMN fractals_cache.delta_4h IS 'Filtered delta over 4 hours';
COMMENT ON COLUMN fractals_cache.delta_24h IS 'Filtered delta over 24 hours';
COMMENT ON COLUMN fractals_cache.oi_delta_24h IS 'Open Interest change over 24 hours';
COMMENT ON COLUMN fractals_cache.orderbook_imbalance IS 'Average orderbook imbalance';
COMMENT ON COLUMN fractals_cache.confidence_score IS 'Signal confidence 0-100';
COMMENT ON COLUMN fractals_cache.enriched_at IS 'Timestamp when fractal was enriched with Delta data';

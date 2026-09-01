-- ============================================================================
-- Migration 004: Create Fractals Cache table
-- Source: docs/tz/delta_hedger_bot.tz.md (implied dependency)
-- Date: 2026-01-17
-- ============================================================================

CREATE TABLE IF NOT EXISTS fractals_cache (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    base_coin VARCHAR(10) NOT NULL DEFAULT 'BTC',
    timeframe VARCHAR(5) NOT NULL, -- 'H1', 'H4'
    type VARCHAR(5) NOT NULL, -- 'HIGH', 'LOW'
    price DECIMAL(18, 8) NOT NULL,
    is_key_fractal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE fractals_cache IS 'Cache of detected fractals for signal detection';
COMMENT ON COLUMN fractals_cache.type IS 'HIGH (resistance) or LOW (support)';
COMMENT ON COLUMN fractals_cache.is_key_fractal IS 'Flag for significant fractals used for breakout detection';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_fractals_lookup 
ON fractals_cache (base_coin, timeframe, is_key_fractal, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_fractals_timestamp 
ON fractals_cache (timestamp DESC);

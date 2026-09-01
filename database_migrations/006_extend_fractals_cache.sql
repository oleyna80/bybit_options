-- ============================================================================
-- Migration 006: Extend fractals_cache for Fractal Collector (FRAC-003)
-- Date: 2026-01-18
-- ============================================================================

ALTER TABLE fractals_cache
    ADD COLUMN IF NOT EXISTS symbol TEXT,
    ADD COLUMN IF NOT EXISTS candle_time TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS fractal_type VARCHAR(5),
    ADD COLUMN IF NOT EXISTS bb_upper_1sigma NUMERIC,
    ADD COLUMN IF NOT EXISTS bb_lower_1sigma NUMERIC,
    ADD COLUMN IF NOT EXISTS bb_upper_2sigma NUMERIC,
    ADD COLUMN IF NOT EXISTS bb_lower_2sigma NUMERIC,
    ADD COLUMN IF NOT EXISTS alligator_teeth NUMERIC;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fractals_cache_symbol_timeframe_type_time
    ON fractals_cache (symbol, timeframe, fractal_type, candle_time);

CREATE INDEX IF NOT EXISTS idx_fractals_cache_symbol_timeframe_key_time
    ON fractals_cache (symbol, timeframe, is_key_fractal, candle_time DESC);

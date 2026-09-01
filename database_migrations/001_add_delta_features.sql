-- ============================================================================
-- DELTA ANALYTICS DATABASE MIGRATION
-- ============================================================================
-- Purpose: Add missing features to existing delta_analytics_db tables
-- Database: delta_analytics_db
-- Execution: psql -h localhost -U trading_user -d delta_analytics_db -f 001_add_delta_features.sql
-- ============================================================================

-- Check TimescaleDB version
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

-- ============================================================================
-- FIX 1: Convert large_trades to hypertable (if not already)
-- ============================================================================

-- Check if already hypertable
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'large_trades'
    ) THEN
        PERFORM create_hypertable(
            'large_trades',
            'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
        RAISE NOTICE 'large_trades converted to hypertable';
    ELSE
        RAISE NOTICE 'large_trades already a hypertable';
    END IF;
END $$;

-- ============================================================================
-- FIX 2: Add missing indexes if not exist
-- ============================================================================

-- Index for exchange + symbol queries
CREATE INDEX IF NOT EXISTS idx_large_trades_exchange_symbol_time 
ON large_trades (exchange, symbol, timestamp DESC);

-- Index for filtering very large trades
CREATE INDEX IF NOT EXISTS idx_large_trades_side_time 
ON large_trades (side, timestamp DESC) 
WHERE quantity >= 10;

-- Index for quantity-based queries
CREATE INDEX IF NOT EXISTS idx_large_trades_quantity 
ON large_trades (quantity DESC, timestamp DESC);

-- Index for orderbook snapshots
CREATE INDEX IF NOT EXISTS idx_orderbook_exchange_symbol_time 
ON orderbook_snapshots (exchange, symbol, timestamp DESC);

-- Index for high imbalance detection
CREATE INDEX IF NOT EXISTS idx_orderbook_imbalance 
ON orderbook_snapshots (imbalance, timestamp DESC) 
WHERE ABS(imbalance) > 0.5;

-- GIN indexes for JSONB orderbook data
CREATE INDEX IF NOT EXISTS idx_orderbook_bids_gin 
ON orderbook_snapshots USING GIN (bids);

CREATE INDEX IF NOT EXISTS idx_orderbook_asks_gin 
ON orderbook_snapshots USING GIN (asks);

-- Indexes for delta_metrics
CREATE INDEX IF NOT EXISTS idx_delta_metrics_exchange_symbol_interval_time 
ON delta_metrics (exchange, symbol, interval, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_delta_metrics_filtered_delta 
ON delta_metrics (ABS(filtered_delta) DESC, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_delta_metrics_imbalance 
ON delta_metrics (ABS(avg_imbalance) DESC, timestamp DESC);

-- ============================================================================
-- FIX 3: Create or refresh continuous aggregates
-- ============================================================================

-- Drop existing if corrupt
DROP MATERIALIZED VIEW IF EXISTS delta_metrics_1m CASCADE;
DROP MATERIALIZED VIEW IF EXISTS delta_metrics_5m CASCADE;

-- Recreate 1-minute aggregate
CREATE MATERIALIZED VIEW delta_metrics_1m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS filtered_buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS filtered_sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) - 
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS filtered_delta,
    COUNT(*) AS large_trades_count,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    SUM(quantity) AS total_volume
FROM large_trades
GROUP BY bucket, exchange, symbol;

-- Add refresh policy for 1-minute aggregate
SELECT add_continuous_aggregate_policy('delta_metrics_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '10 seconds',
    schedule_interval => INTERVAL '30 seconds',
    if_not_exists => TRUE
);

-- Recreate 5-minute aggregate
CREATE MATERIALIZED VIEW delta_metrics_5m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS filtered_buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS filtered_sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) - 
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS filtered_delta,
    COUNT(*) AS large_trades_count,
    AVG(price) AS avg_price,
    STDDEV(price) AS price_volatility,
    SUM(quantity) AS total_volume
FROM large_trades
GROUP BY bucket, exchange, symbol;

-- Add refresh policy for 5-minute aggregate
SELECT add_continuous_aggregate_policy('delta_metrics_5m',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- ============================================================================
-- FIX 4: Verify retention policies exist
-- ============================================================================

-- Add retention policy for large_trades if not exists
SELECT add_retention_policy('large_trades', INTERVAL '90 days', if_not_exists => TRUE);

-- Add retention policy for orderbook_snapshots if not exists
SELECT add_retention_policy('orderbook_snapshots', INTERVAL '30 days', if_not_exists => TRUE);

-- Add retention policy for delta_metrics if not exists
SELECT add_retention_policy('delta_metrics', INTERVAL '365 days', if_not_exists => TRUE);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check all hypertables
SELECT hypertable_name, num_chunks 
FROM timescaledb_information.hypertables
ORDER BY hypertable_name;

-- Check continuous aggregates
SELECT view_name, materialization_hypertable_name
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;

-- Check all jobs (retention + refresh policies)
SELECT 
    job_id,
    application_name,
    schedule_interval,
    config->>'hypertable_name' as target_table
FROM timescaledb_information.jobs
ORDER BY job_id;

-- Check indexes
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('large_trades', 'orderbook_snapshots', 'delta_metrics')
ORDER BY tablename, indexname;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Delta Analytics migration completed successfully!';
    RAISE NOTICE 'Tables: large_trades, orderbook_snapshots, delta_metrics';
    RAISE NOTICE 'Continuous aggregates: delta_metrics_1m, delta_metrics_5m';
    RAISE NOTICE 'Retention policies: 90d, 30d, 365d';
END $$;

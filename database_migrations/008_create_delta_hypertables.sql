-- ============================================================================
-- Migration: 008_create_delta_hypertables.sql
-- Description: Create TimescaleDB hypertables for Delta Volume Analytics
-- Author: Roo
-- Date: 2026-01-19
-- ============================================================================

-- Ensure TimescaleDB extension is enabled
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- TABLE: large_trades
-- ============================================================================
CREATE TABLE IF NOT EXISTS large_trades (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL CHECK (exchange IN ('bybit', 'deribit', 'binance')),
    market_type VARCHAR(20) NOT NULL CHECK (market_type IN ('spot', 'perpetual', 'futures')),
    symbol VARCHAR(50) NOT NULL,
    trade_id VARCHAR(100) NOT NULL,
    price NUMERIC(20, 8) NOT NULL CHECK (price > 0),
    quantity NUMERIC(20, 8) NOT NULL CHECK (quantity > 0),
    side VARCHAR(10) NOT NULL CHECK (side IN ('Buy', 'Sell')),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT pk_large_trades PRIMARY KEY (timestamp, exchange, trade_id)
);

SELECT create_hypertable(
    'large_trades',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_large_trades_symbol_time
ON large_trades (symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_large_trades_side_time
ON large_trades (side, timestamp DESC);

-- ============================================================================
-- TABLE: orderbook_snapshots
-- ============================================================================
CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    bid_volume_total NUMERIC(20, 8) NOT NULL,
    ask_volume_total NUMERIC(20, 8) NOT NULL,
    imbalance NUMERIC(5, 4) NOT NULL CHECK (imbalance >= -1 AND imbalance <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT pk_orderbook_snapshots PRIMARY KEY (timestamp, exchange, symbol)
);

SELECT create_hypertable(
    'orderbook_snapshots',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_time
ON orderbook_snapshots (symbol, timestamp DESC);

-- ============================================================================
-- TABLE: open_interest
-- ============================================================================
CREATE TABLE IF NOT EXISTS open_interest (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    open_interest NUMERIC(20, 8) NOT NULL,
    open_interest_value NUMERIC(20, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT pk_open_interest PRIMARY KEY (timestamp, exchange, symbol)
);

SELECT create_hypertable(
    'open_interest',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_oi_symbol_time
ON open_interest (symbol, timestamp DESC);

-- ============================================================================
-- TABLE: delta_config
-- ============================================================================
CREATE TABLE IF NOT EXISTS delta_config (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    threshold_qty NUMERIC(20, 8) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO delta_config (symbol, threshold_qty) VALUES
    ('BTCUSDT', 5.0),
    ('ETHUSDT', 50.0)
ON CONFLICT (symbol) DO NOTHING;

-- ============================================================================
-- CONTINUOUS AGGREGATE: delta_metrics_1m
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS delta_metrics_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE -quantity END) AS filtered_delta,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM large_trades
GROUP BY bucket, exchange, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('delta_metrics_1m',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '10 seconds',
    schedule_interval => INTERVAL '30 seconds',
    if_not_exists => TRUE
);

-- ============================================================================
-- CONTINUOUS AGGREGATE: delta_metrics_5m
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS delta_metrics_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE -quantity END) AS filtered_delta,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price
FROM large_trades
GROUP BY bucket, exchange, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('delta_metrics_5m',
    start_offset => INTERVAL '6 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- ============================================================================
-- CONTINUOUS AGGREGATE: delta_metrics_1h
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS delta_metrics_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE -quantity END) AS filtered_delta,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price
FROM large_trades
GROUP BY bucket, exchange, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('delta_metrics_1h',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

-- ============================================================================
-- RETENTION POLICIES
-- ============================================================================
SELECT add_retention_policy('large_trades', INTERVAL '180 days', if_not_exists => TRUE);
SELECT add_retention_policy('orderbook_snapshots', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('open_interest', INTERVAL '365 days', if_not_exists => TRUE);

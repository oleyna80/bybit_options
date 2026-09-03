-- Create large_trades table
CREATE TABLE IF NOT EXISTS large_trades (
    id BIGSERIAL,
    exchange VARCHAR(50) NOT NULL,
    market_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    price NUMERIC(18, 8) NOT NULL,
    quantity NUMERIC(18, 8) NOT NULL,
    side VARCHAR(10) NOT NULL,
    trade_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (exchange, trade_id, timestamp)
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable(
    'large_trades',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- Create orderbook_snapshots table
CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    id BIGSERIAL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    bid_volume_total NUMERIC(18, 8) NOT NULL,
    ask_volume_total NUMERIC(18, 8) NOT NULL,
    imbalance NUMERIC(5, 4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (exchange, symbol, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable(
    'orderbook_snapshots',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_large_trades_symbol_time ON large_trades (exchange, symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_time ON orderbook_snapshots (exchange, symbol, timestamp DESC);

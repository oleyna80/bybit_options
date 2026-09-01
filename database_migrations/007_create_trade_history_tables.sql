-- Migration 007: Trade history schema (orders, portfolio_snapshots) + additive trades расширение

-- Таблица orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(64) UNIQUE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20),
    qty NUMERIC NOT NULL,
    price NUMERIC,
    avg_price NUMERIC,
    cum_exec_qty NUMERIC,
    cum_exec_fee NUMERIC,
    status VARCHAR(20) NOT NULL,
    created_time TIMESTAMPTZ NOT NULL,
    updated_time TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_symbol_time ON orders (symbol, created_time DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);

-- Таблица portfolio_snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMPTZ NOT NULL,
    equity NUMERIC NOT NULL,
    available_balance NUMERIC,
    margin_used NUMERIC,
    total_delta NUMERIC,
    total_gamma NUMERIC,
    total_vega NUMERIC,
    total_theta NUMERIC,
    btc_price NUMERIC,
    positions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_time ON portfolio_snapshots (snapshot_time DESC);

-- Additive расширение trades
ALTER TABLE trades
    ADD COLUMN IF NOT EXISTS category TEXT,
    ADD COLUMN IF NOT EXISTS raw_data JSONB,
    -- Алиас-поля для совместимости с AC (nullable, не ломаем старые)
    ADD COLUMN IF NOT EXISTS exec_time TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS qty NUMERIC,
    ADD COLUMN IF NOT EXISTS price NUMERIC,
    ADD COLUMN IF NOT EXISTS exec_fee NUMERIC;

CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_category_timestamp ON trades (category, timestamp DESC);

-- VERIFY:
-- 1) Таблицы: orders, portfolio_snapshots
-- 2) Колонки в trades: category, raw_data, exec_time, qty, price, exec_fee
-- 3) Индексы: idx_orders_symbol_time, idx_orders_status, idx_portfolio_time,
--    idx_trades_symbol_timestamp, idx_trades_category_timestamp

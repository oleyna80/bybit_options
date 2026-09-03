-- Создание базовой таблицы trades
CREATE TABLE IF NOT EXISTS trades (
    exec_id VARCHAR(100) PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    size NUMERIC(18, 8) NOT NULL,
    exec_price NUMERIC(18, 8) NOT NULL,
    fee NUMERIC(18, 8) NOT NULL,
    role VARCHAR(10) NOT NULL,
    iv NUMERIC(10, 6),
    underlying_price NUMERIC(18, 8),
    strategy_tag VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side);

-- Комментарий
COMMENT ON TABLE trades IS 'Trade execution history from Bybit';

-- Position Entry Tracking (for IV logging)
CREATE TABLE IF NOT EXISTS position_entries (
    symbol VARCHAR(50) PRIMARY KEY,
    entry_price DECIMAL(18,8) NOT NULL,
    entry_iv DECIMAL(10,6),              -- Weighted average Mark IV (stored as fraction: 0.52 = 52%)
    net_qty DECIMAL(18,8) NOT NULL,      -- Net position (positive = long, negative = short)
    abs_qty DECIMAL(18,8) NOT NULL,      -- Absolute quantity for averaging
    entry_time TIMESTAMPTZ NOT NULL,     -- First fill time
    last_update TIMESTAMPTZ NOT NULL,    -- Last fill time
    fill_count INT DEFAULT 1,            -- Number of partial fills
    position_side VARCHAR(10) NOT NULL,  -- 'LONG' or 'SHORT' (initial direction)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_symbol ON position_entries (symbol);

-- Comments
COMMENT ON TABLE position_entries IS 'Tracks entry IV for open positions with weighted averaging for partial fills. Supports both LONG and SHORT positions.';
COMMENT ON COLUMN position_entries.entry_iv IS 'Weighted average Mark IV across all fills (stored as fraction: 0.52 = 52%)';
COMMENT ON COLUMN position_entries.net_qty IS 'Net position quantity (positive = long, negative = short)';
COMMENT ON COLUMN position_entries.position_side IS 'Initial position direction (LONG opened by Buy, SHORT opened by Sell)';

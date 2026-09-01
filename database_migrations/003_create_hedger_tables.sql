-- ============================================================================
-- Migration 003: Create Delta Hedger Bot tables
-- Source: docs/tz/delta_hedger_bot.tz.md (APPROVED)
-- Date: 2026-01-17
-- ============================================================================

-- ============================================================================
-- Table: hedge_actions
-- Description: Log of all hedging actions taken by Delta Hedger Bot
-- ============================================================================
CREATE TABLE IF NOT EXISTS hedge_actions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Context
    mode VARCHAR(20) NOT NULL,  -- 'NEUTRAL', 'DIRECTIONAL', 'DEFENSIVE'
    trigger_source VARCHAR(20), -- 'H1_FRACTAL', 'H4_FRACTAL', 'THRESHOLD', 'MANUAL'
    fractal_price DECIMAL(12, 2),
    fractal_timeframe VARCHAR(3),
    
    -- Position before action
    delta_before DECIMAL(18, 8) NOT NULL,
    target_delta DECIMAL(18, 8) NOT NULL,
    
    -- Action details
    action_type VARCHAR(20) NOT NULL,  -- 'FUTURES_HEDGE', 'OPTIONS_BUY', 'SKIP'
    instrument VARCHAR(50),
    side VARCHAR(10),  -- 'BUY', 'SELL'
    size DECIMAL(18, 8),
    order_type VARCHAR(20),  -- 'LIMIT', 'MARKET'
    limit_price DECIMAL(18, 8),
    
    -- Result
    order_id VARCHAR(100),
    exec_price DECIMAL(18, 8),
    delta_after DECIMAL(18, 8),
    status VARCHAR(20) NOT NULL,  -- 'PLACED', 'FILLED', 'CANCELLED', 'FAILED'
    error_message TEXT,
    
    -- Metadata
    execution_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE hedge_actions IS 'Log of all hedging actions taken by Delta Hedger Bot';
COMMENT ON COLUMN hedge_actions.mode IS 'Operating mode: NEUTRAL, DIRECTIONAL, DEFENSIVE';
COMMENT ON COLUMN hedge_actions.trigger_source IS 'What triggered this action: H1_FRACTAL, H4_FRACTAL, THRESHOLD, MANUAL';
COMMENT ON COLUMN hedge_actions.delta_before IS 'Portfolio delta before hedge action in BTC';
COMMENT ON COLUMN hedge_actions.target_delta IS 'Target delta for the current mode in BTC';
COMMENT ON COLUMN hedge_actions.action_type IS 'Type of action: FUTURES_HEDGE, OPTIONS_BUY, SKIP';
COMMENT ON COLUMN hedge_actions.execution_time_ms IS 'Time taken to execute the action in milliseconds';

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_hedge_actions_time ON hedge_actions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_hedge_actions_mode ON hedge_actions(mode, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_hedge_actions_status ON hedge_actions(status);
CREATE INDEX IF NOT EXISTS idx_hedge_actions_trigger ON hedge_actions(trigger_source, timestamp DESC);

-- ============================================================================
-- Table: hedger_config
-- Description: Runtime configuration for Delta Hedger Bot
-- ============================================================================
CREATE TABLE IF NOT EXISTS hedger_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comment
COMMENT ON TABLE hedger_config IS 'Runtime configuration for Delta Hedger Bot';

-- Insert initial configuration values
INSERT INTO hedger_config (key, value, description) VALUES
    ('mode', 'NEUTRAL', 'Current operating mode: NEUTRAL, DIRECTIONAL, DEFENSIVE'),
    ('target_delta', '0.0', 'Target delta in BTC'),
    ('threshold', '0.003', 'Rebalance threshold in BTC'),
    ('directional_bias_long', '0.01', 'Delta bias for DIRECTIONAL mode LONG (BTC)'),
    ('directional_bias_short', '-0.01', 'Delta bias for DIRECTIONAL mode SHORT (BTC)'),
    ('enabled', 'false', 'Is bot enabled (true/false)'),
    ('check_interval_seconds', '60', 'How often to check delta (seconds)'),
    ('max_order_size', '0.1', 'Maximum single order size in BTC'),
    ('limit_price_offset_bps', '5', 'Limit price offset in basis points'),
    ('emergency_delta_threshold', '0.5', 'Delta threshold for emergency hedge in BTC'),
    ('max_retries', '3', 'Maximum order placement retries'),
    ('retry_delay_base', '1.0', 'Base delay for exponential backoff (seconds)')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Verification query (optional - run to verify migration)
-- ============================================================================
-- SELECT table_name FROM information_schema.tables WHERE table_name IN ('hedge_actions', 'hedger_config');
-- SELECT * FROM hedger_config;

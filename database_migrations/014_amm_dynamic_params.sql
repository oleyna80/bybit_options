-- Migration: 014_amm_dynamic_params.sql
-- Description: Add dynamic parameters for AMM strategies and agent commands audit log
-- Date: 2026-01-24

-- ============================================================================
-- 1. Add dynamic parameters to amm_strategies
-- ============================================================================

ALTER TABLE amm_strategies
ADD COLUMN IF NOT EXISTS skew_factor DECIMAL(10, 4) DEFAULT 0.0;

ALTER TABLE amm_strategies
ADD COLUMN IF NOT EXISTS spread_bps INTEGER DEFAULT 50;

ALTER TABLE amm_strategies
ADD COLUMN IF NOT EXISTS min_iv DECIMAL(10, 4) DEFAULT 0.10;

ALTER TABLE amm_strategies
ADD COLUMN IF NOT EXISTS max_iv DECIMAL(10, 4) DEFAULT 2.00;

ALTER TABLE amm_strategies
ADD COLUMN IF NOT EXISTS last_agent_update TIMESTAMPTZ;

-- Add comments
COMMENT ON COLUMN amm_strategies.skew_factor IS 
'Skew adjustment: final_iv = target_iv + skew_factor * delta';

COMMENT ON COLUMN amm_strategies.spread_bps IS 
'Bid-ask spread in basis points (50 = 0.5%)';

COMMENT ON COLUMN amm_strategies.min_iv IS 
'Minimum IV floor for pricing';

COMMENT ON COLUMN amm_strategies.max_iv IS 
'Maximum IV cap for pricing';

COMMENT ON COLUMN amm_strategies.last_agent_update IS 
'Timestamp of last update from Trading Expert agent';


-- ============================================================================
-- 2. Create agent commands audit log
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_commands_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    command_type VARCHAR(50) NOT NULL,
    strategy_id INTEGER REFERENCES amm_strategies(id) ON DELETE SET NULL,
    
    -- What changed
    old_params JSONB,
    new_params JSONB,
    
    -- Source
    source VARCHAR(20) DEFAULT 'MANUAL',
    reason TEXT,
    
    -- Result
    status VARCHAR(20) DEFAULT 'EXECUTED'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_commands_strategy 
ON agent_commands_log(strategy_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_agent_commands_timestamp
ON agent_commands_log(timestamp DESC);

-- Comments
COMMENT ON TABLE agent_commands_log IS 
'Audit log for all commands from Trading Expert agent to AMM Robot';

COMMENT ON COLUMN agent_commands_log.command_type IS 
'Type: UPDATE_STRATEGY_PARAMS, PAUSE_STRATEGY, RESUME_STRATEGY, etc.';

COMMENT ON COLUMN agent_commands_log.source IS 
'MANUAL (human via chat) or AUTO (automated strategy loop)';

COMMENT ON COLUMN agent_commands_log.reason IS 
'Explanation from agent why this command was issued';


-- ============================================================================
-- 3. Create operating mode table
-- ============================================================================

CREATE TABLE IF NOT EXISTS amm_operating_mode (
    id SERIAL PRIMARY KEY,
    mode VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    check_interval_minutes INTEGER DEFAULT 15,
    last_auto_check TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default mode
INSERT INTO amm_operating_mode (mode, check_interval_minutes)
VALUES ('MANUAL', 15)
ON CONFLICT DO NOTHING;

-- Index
CREATE INDEX IF NOT EXISTS idx_amm_mode_updated 
ON amm_operating_mode(updated_at DESC);

COMMENT ON TABLE amm_operating_mode IS 
'Current operating mode for AMM: MANUAL or AUTO';

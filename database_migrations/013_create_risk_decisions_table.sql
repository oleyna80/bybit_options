-- AMM Gatekeeper: Risk Decisions Audit Log
-- Creates table for tracking all risk management decisions
-- Author: Tech Lead
-- Date: 2026-01-24

-- =====================================================
-- 1. Risk Decisions Table
-- =====================================================

CREATE TABLE IF NOT EXISTS risk_decisions (
    id SERIAL PRIMARY KEY,
    decision_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decision_type VARCHAR(20) NOT NULL,  -- 'PORTFOLIO' / 'LEG'
    decision VARCHAR(10) NOT NULL,        -- 'ALLOW' / 'BLOCK'
    
    -- Context
    strategy_id INTEGER REFERENCES amm_strategies(id),
    leg_id INTEGER REFERENCES amm_legs(id),
    
    -- Risk metrics at decision time
    portfolio_delta DECIMAL(10, 4),
    portfolio_gamma DECIMAL(10, 6),
    portfolio_vega DECIMAL(10, 2),
    
    -- Limits
    delta_limit DECIMAL(10, 4),
    gamma_limit DECIMAL(10, 6),
    vega_limit DECIMAL(10, 2),
    
    -- Reason
    reason TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. Indexes for Performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_risk_decisions_time 
ON risk_decisions(decision_time DESC);

CREATE INDEX IF NOT EXISTS idx_risk_decisions_type 
ON risk_decisions(decision_type, decision);

CREATE INDEX IF NOT EXISTS idx_risk_decisions_strategy
ON risk_decisions(strategy_id)
WHERE strategy_id IS NOT NULL;

-- =====================================================
-- 3. Comments and Documentation
-- =====================================================

COMMENT ON TABLE risk_decisions IS 
'Audit log for all Gatekeeper risk decisions (ALLOW/BLOCK). 
Tracks portfolio-level and per-leg risk evaluations.';

COMMENT ON COLUMN risk_decisions.decision_type IS 
'Type of decision: PORTFOLIO (portfolio-level gate) or LEG (per-leg gate)';

COMMENT ON COLUMN risk_decisions.decision IS 
'Outcome: ALLOW (order can proceed) or BLOCK (order rejected due to risk)';

COMMENT ON COLUMN risk_decisions.reason IS 
'Human-readable explanation for BLOCK decisions';

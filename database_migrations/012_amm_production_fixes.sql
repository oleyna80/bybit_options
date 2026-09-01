-- AMM Production Fixes Migration
-- Creates unified trade log view and necessary indexes
-- Author: Tech Lead
-- Date: 2026-01-23

-- =====================================================
-- 1. Add caching fields to amm_legs
-- =====================================================

ALTER TABLE amm_legs ADD COLUMN IF NOT EXISTS 
    expiry_date DATE NULL;

ALTER TABLE amm_legs ADD COLUMN IF NOT EXISTS 
    current_delta DECIMAL(10, 6) DEFAULT 0;

-- =====================================================
-- 2. Add indexes for performance
-- =====================================================

-- Index for reconciliation (fast lookup by orderLinkId)
CREATE INDEX IF NOT EXISTS idx_amm_orders_link_id 
ON amm_orders(bybit_order_link_id);

-- Index for unified_trades view performance (orders table)
CREATE INDEX IF NOT EXISTS idx_orders_created_time
ON orders(created_time DESC);

-- =====================================================
-- 3. Unified Trade Log View
-- =====================================================

CREATE OR REPLACE VIEW unified_trades AS
SELECT 
    'AMM'::VARCHAR AS source,
    ao.bybit_order_id AS order_id,
    al.symbol,
    al.side,
    ao.price::FLOAT AS price,
    ao.status,
    ao.last_updated AS timestamp,
    ast.name AS strategy_name,
    ao.iv_at_creation AS iv
FROM amm_orders ao
JOIN amm_legs al ON ao.leg_id = al.id
JOIN amm_strategies ast ON al.strategy_id = ast.id

UNION ALL

SELECT
    'MANUAL'::VARCHAR AS source,
    o.order_id,
    o.symbol,
    o.side,
    o.avg_price AS price,
    o.status,
    o.created_time AS timestamp,
    NULL AS strategy_name,
    NULL AS iv
FROM orders o
WHERE o.status = 'Filled';

-- =====================================================
-- 4. Comments and documentation
-- =====================================================

COMMENT ON VIEW unified_trades IS 
'Unified trade log (AMM + Manual) for Trading Expert audit. 
Combines trades from automated AMM strategies and manual entries from the orders table.';

COMMENT ON COLUMN amm_legs.expiry_date IS 
'Cached expiry date parsed from symbol to avoid repeated parsing';

COMMENT ON COLUMN amm_legs.current_delta IS 
'Last calculated delta for this leg, updated on each gardener cycle';

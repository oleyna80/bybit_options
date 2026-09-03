-- AMM Strategy Logic
-- Stores the high-level configuration for a Market Maker instance
CREATE TABLE IF NOT EXISTS amm_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,            -- e.g. "June Income", "BTC Strangle"
    sub_account_id VARCHAR(50),            -- If we support multiple accounts later
    
    -- Status
    is_active BOOLEAN DEFAULT FALSE,       -- Master Switch
    is_paused BOOLEAN DEFAULT FALSE,       -- Gating Switch (temp pause)
    pause_reason TEXT,                     -- e.g. "Delta Limit Exceeded"
    
    -- Pricing Config
    target_iv DECIMAL(10, 4) NOT NULL,     -- User Defined Fair Vol (e.g. 0.4550)
    skew_factor DECIMAL(10, 4) DEFAULT 0,  -- Auto-adjust IV based on Delta?
    
    -- Risk Limits
    max_delta DECIMAL(10, 4) DEFAULT 1.0,  -- Portfolio Delta Cap
    max_gamma DECIMAL(10, 4) DEFAULT 2.0,  -- Gamma Cap
    max_vega  DECIMAL(10, 4) DEFAULT 500,  -- Vega Cap
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- AMM Legs
-- Defines the structure. One Strategy has many Legs.
CREATE TABLE IF NOT EXISTS amm_legs (
    id SERIAL PRIMARY KEY,
    strategy_id INT REFERENCES amm_strategies(id) ON DELETE CASCADE,
    
    symbol VARCHAR(50) NOT NULL,           -- e.g. BTC-26JUN26-100000-C-USDT
    side VARCHAR(10) NOT NULL,             -- BUY / SELL
    ratio DECIMAL(10, 4) DEFAULT 1.0,      -- Quantity Ratio (e.g. 1 for Call, -2 for Ratio Spread)
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,        -- Can be paused individually (Leg Gating)
    total_filled DECIMAL(20, 8) DEFAULT 0, -- Cumulative fills for this leg
    target_size DECIMAL(20, 8) DEFAULT 0,  -- How much we want to accumulate total
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AMM Orders
-- Tracks the specific active orders managed by the bot
CREATE TABLE IF NOT EXISTS amm_orders (
    id SERIAL PRIMARY KEY,
    leg_id INT REFERENCES amm_legs(id) ON DELETE CASCADE,
    
    -- Exchange Info
    bybit_order_id VARCHAR(100),
    bybit_order_link_id VARCHAR(100) UNIQUE, -- Our idempotent ID
    
    -- Snapshot at creation
    price DECIMAL(20, 8),
    iv_at_creation DECIMAL(10, 4),           -- What IV we priced this at
    
    status VARCHAR(20) DEFAULT 'NEW',        -- NEW, ACTIVE, FILLED, CANCELLED
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Speed
CREATE INDEX idx_amm_legs_strategy ON amm_legs(strategy_id);
CREATE INDEX idx_amm_orders_leg ON amm_orders(leg_id);
CREATE INDEX idx_amm_orders_status ON amm_orders(status);

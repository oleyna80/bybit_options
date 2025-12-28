-- DVOL History (Deribit Volatility Index)
CREATE TABLE IF NOT EXISTS dvol_history (
    timestamp TIMESTAMPTZ PRIMARY KEY,
    dvol DECIMAL(6,2) NOT NULL,
    ivr DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('dvol_history', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_dvol_timestamp ON dvol_history (timestamp DESC);

-- Fractals Cache (Williams Fractals for D1/H4/H1)
CREATE TABLE IF NOT EXISTS fractals_cache (
    id SERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(3) NOT NULL,
    base_coin VARCHAR(10) NOT NULL,
    type VARCHAR(10) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    is_key_fractal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, timeframe, base_coin, type)
);

CREATE INDEX IF NOT EXISTS idx_fractals_timeframe_coin
    ON fractals_cache (timeframe, base_coin, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fractals_key
    ON fractals_cache (base_coin, timeframe, is_key_fractal)
    WHERE is_key_fractal = TRUE;

-- Bollinger Bands History
CREATE TABLE IF NOT EXISTS bollinger_bands_history (
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(3) NOT NULL,
    base_coin VARCHAR(10) NOT NULL,
    upper_2sigma DECIMAL(12,2),
    upper_1sigma DECIMAL(12,2),
    middle DECIMAL(12,2),
    lower_1sigma DECIMAL(12,2),
    lower_2sigma DECIMAL(12,2),
    bb_width DECIMAL(8,4),
    PRIMARY KEY (timestamp, timeframe, base_coin)
);

SELECT create_hypertable('bollinger_bands_history', 'timestamp', if_not_exists => TRUE);

-- Market Regime History (D1 decisions)
CREATE TABLE IF NOT EXISTS market_regime_history (
    timestamp TIMESTAMPTZ PRIMARY KEY,
    base_coin VARCHAR(10) NOT NULL,
    regime VARCHAR(20) NOT NULL,
    key_support DECIMAL(12,2),
    key_resistance DECIMAL(12,2),
    squeeze_active BOOLEAN DEFAULT FALSE,
    vol_risk VARCHAR(10),
    recommended_strategy VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regime_coin_time
    ON market_regime_history (base_coin, timestamp DESC);

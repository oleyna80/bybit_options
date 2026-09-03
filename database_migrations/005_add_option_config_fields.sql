-- Add new config fields for Defensive Mode
-- option_price_markup_pct: Percentage markup for option limit orders (default 5.0%)
-- hedge_base_coin: Base coin for hedging (default 'BTC')

ALTER TABLE hedger_config
ADD COLUMN IF NOT EXISTS option_price_markup_pct FLOAT DEFAULT 5.0,
ADD COLUMN IF NOT EXISTS hedge_base_coin VARCHAR(10) DEFAULT 'BTC';

-- Update existing records to have defaults (if any, usually only one singleton row exists)
UPDATE hedger_config 
SET option_price_markup_pct = 5.0, hedge_base_coin = 'BTC' 
WHERE option_price_markup_pct IS NULL;

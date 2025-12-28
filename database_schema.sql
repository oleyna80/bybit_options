-- ============================================================================
-- IV Rank Feature Database Schema
-- PostgreSQL 15 + TimescaleDB
-- ============================================================================

-- Таблица для OHLCV данных бессрочного фьючерса
CREATE TABLE IF NOT EXISTS perpetual_ohlcv (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL DEFAULT 'BTCUSDT',
    open DECIMAL(12, 2) NOT NULL,
    high DECIMAL(12, 2) NOT NULL,
    low DECIMAL(12, 2) NOT NULL,
    close DECIMAL(12, 2) NOT NULL,
    volume DECIMAL(18, 4) NOT NULL,
    turnover DECIMAL(20, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol)
);

-- Создание hypertable для временных рядов
SELECT create_hypertable(
    'perpetual_ohlcv', 
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);

-- Индекс для быстрого поиска по символу
CREATE INDEX IF NOT EXISTS idx_perpetual_symbol_time 
ON perpetual_ohlcv (symbol, timestamp DESC);

-- ============================================================================

-- Таблица для IV данных опционов
CREATE TABLE IF NOT EXISTS option_iv_daily (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    underlying VARCHAR(20) NOT NULL DEFAULT 'BTC',
    strike DECIMAL(12, 2) NOT NULL,
    expiry_date DATE NOT NULL,
    days_to_expiry INT NOT NULL,
    option_type CHAR(1) NOT NULL CHECK (option_type IN ('C', 'P')),
    iv DECIMAL(8, 4) NOT NULL CHECK (iv >= 0),
    mark_price DECIMAL(18, 8),
    mark_iv DECIMAL(8, 4),
    bid_price DECIMAL(18, 8),
    ask_price DECIMAL(18, 8),
    bid_iv DECIMAL(8, 4),
    ask_iv DECIMAL(8, 4),
    delta DECIMAL(8, 6),
    gamma DECIMAL(10, 8),
    vega DECIMAL(10, 6),
    theta DECIMAL(10, 6),
    volume DECIMAL(18, 4),
    turnover DECIMAL(20, 4),
    open_interest DECIMAL(18, 4),
    is_atm BOOLEAN DEFAULT FALSE,
    distance_to_atm DECIMAL(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol)
);

-- Создание hypertable
SELECT create_hypertable(
    'option_iv_daily', 
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_option_iv_underlying_time 
ON option_iv_daily (underlying, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_option_iv_atm 
ON option_iv_daily (underlying, timestamp, is_atm) 
WHERE is_atm = TRUE;

CREATE INDEX IF NOT EXISTS idx_option_iv_expiry 
ON option_iv_daily (underlying, days_to_expiry, timestamp DESC)
WHERE days_to_expiry BETWEEN 25 AND 35;

-- ============================================================================

-- Таблица для рассчитанного IV Rank
CREATE TABLE IF NOT EXISTS iv_rank_daily (
    timestamp TIMESTAMPTZ NOT NULL PRIMARY KEY,
    underlying VARCHAR(20) NOT NULL DEFAULT 'BTC',
    current_iv DECIMAL(8, 4) NOT NULL CHECK (current_iv >= 0),
    min_iv_30d DECIMAL(8, 4) NOT NULL CHECK (min_iv_30d >= 0),
    max_iv_30d DECIMAL(8, 4) NOT NULL CHECK (max_iv_30d >= 0),
    mean_iv_30d DECIMAL(8, 4),
    median_iv_30d DECIMAL(8, 4),
    stddev_iv_30d DECIMAL(8, 4),
    iv_rank DECIMAL(5, 2) NOT NULL CHECK (iv_rank >= 0 AND iv_rank <= 100),
    data_points_count INT NOT NULL,
    atm_strike DECIMAL(12, 2),
    atm_symbol VARCHAR(50),
    perpetual_close DECIMAL(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Создание hypertable
SELECT create_hypertable(
    'iv_rank_daily', 
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '30 days'
);

-- Индекс для быстрого получения последних значений
CREATE INDEX IF NOT EXISTS idx_iv_rank_underlying_time 
ON iv_rank_daily (underlying, timestamp DESC);

-- ============================================================================

-- Таблица для логирования обновлений данных
CREATE TABLE IF NOT EXISTS data_update_log (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    records_processed INT DEFAULT 0,
    records_failed INT DEFAULT 0,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_update_log_time 
ON data_update_log (start_time DESC);

CREATE INDEX IF NOT EXISTS idx_update_log_status 
ON data_update_log (status, job_type);

-- ============================================================================

-- Таблица для конфигурации и метаданных
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Вставка начальных конфигураций
INSERT INTO system_config (key, value, description) VALUES
('last_perpetual_sync', '2023-01-01T00:00:00Z', 'Последняя синхронизация данных фьючерса'),
('last_option_sync', '2023-01-01T00:00:00Z', 'Последняя синхронизация данных опционов'),
('last_iv_rank_calc', '2023-01-01T00:00:00Z', 'Последний расчёт IV Rank'),
('data_retention_days', '1825', 'Период хранения данных (5 лет)'),
('bybit_rate_limit_per_second', '10', 'Лимит запросов к Bybit API')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_perpetual_ohlcv_updated_at
    BEFORE UPDATE ON perpetual_ohlcv
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_option_iv_daily_updated_at
    BEFORE UPDATE ON option_iv_daily
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_iv_rank_daily_updated_at
    BEFORE UPDATE ON iv_rank_daily
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- Материализованное представление для быстрого доступа к последним ATM IV
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_atm_iv AS
SELECT DISTINCT ON (underlying)
    timestamp,
    underlying,
    symbol,
    strike,
    expiry_date,
    days_to_expiry,
    iv,
    mark_price,
    delta,
    vega,
    volume,
    open_interest
FROM option_iv_daily
WHERE is_atm = TRUE
ORDER BY underlying, timestamp DESC;

CREATE UNIQUE INDEX ON latest_atm_iv (underlying);

-- Функция для обновления материализованного представления
CREATE OR REPLACE FUNCTION refresh_latest_atm_iv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY latest_atm_iv;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- Представление для комбинированных данных (цена + IV Rank)
CREATE OR REPLACE VIEW price_with_iv_rank AS
SELECT 
    p.timestamp,
    p.symbol AS perpetual_symbol,
    p.open,
    p.high,
    p.low,
    p.close,
    p.volume,
    ivr.iv_rank,
    ivr.current_iv,
    ivr.min_iv_30d,
    ivr.max_iv_30d,
    ivr.mean_iv_30d,
    ivr.atm_strike,
    ivr.atm_symbol
FROM perpetual_ohlcv p
LEFT JOIN iv_rank_daily ivr 
    ON DATE_TRUNC('day', p.timestamp) = DATE_TRUNC('day', ivr.timestamp)
    AND p.symbol LIKE CONCAT(ivr.underlying, '%')
ORDER BY p.timestamp DESC;

-- ============================================================================

-- Функция для расчёта IV Rank
CREATE OR REPLACE FUNCTION calculate_iv_rank(
    p_timestamp TIMESTAMPTZ,
    p_underlying VARCHAR(20) DEFAULT 'BTC'
)
RETURNS TABLE(
    timestamp TIMESTAMPTZ,
    current_iv DECIMAL(8,4),
    min_iv DECIMAL(8,4),
    max_iv DECIMAL(8,4),
    iv_rank DECIMAL(5,2)
) AS $$
DECLARE
    v_current_iv DECIMAL(8,4);
    v_min_iv DECIMAL(8,4);
    v_max_iv DECIMAL(8,4);
    v_iv_rank DECIMAL(5,2);
BEGIN
    -- Получаем IV за последние 30 дней
    SELECT 
        COALESCE(
            (SELECT iv FROM option_iv_daily 
             WHERE underlying = p_underlying 
             AND is_atm = TRUE 
             AND DATE_TRUNC('day', timestamp) = DATE_TRUNC('day', p_timestamp)
             ORDER BY ABS(days_to_expiry - 30) 
             LIMIT 1
            ), 0
        ) INTO v_current_iv;
    
    -- Получаем min/max за 30 дней до этой даты
    SELECT 
        MIN(iv),
        MAX(iv)
    INTO v_min_iv, v_max_iv
    FROM option_iv_daily
    WHERE underlying = p_underlying
        AND is_atm = TRUE
        AND timestamp >= p_timestamp - INTERVAL '30 days'
        AND timestamp <= p_timestamp;
    
    -- Расчёт IV Rank
    IF v_max_iv IS NULL OR v_min_iv IS NULL OR v_max_iv = v_min_iv THEN
        v_iv_rank := 50.0;
    ELSE
        v_iv_rank := ((v_current_iv - v_min_iv) / (v_max_iv - v_min_iv)) * 100;
        v_iv_rank := GREATEST(0, LEAST(100, v_iv_rank)); -- Clamping
    END IF;
    
    RETURN QUERY SELECT 
        p_timestamp,
        v_current_iv,
        v_min_iv,
        v_max_iv,
        v_iv_rank;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- Функция для очистки старых данных (старше 5 лет)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
DECLARE
    v_retention_days INT;
    v_cutoff_date TIMESTAMPTZ;
    v_deleted_count INT;
BEGIN
    -- Получаем период хранения из конфига
    SELECT value::INT INTO v_retention_days 
    FROM system_config 
    WHERE key = 'data_retention_days';
    
    v_cutoff_date := NOW() - (v_retention_days || ' days')::INTERVAL;
    
    -- Удаление старых данных
    DELETE FROM perpetual_ohlcv WHERE timestamp < v_cutoff_date;
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows from perpetual_ohlcv', v_deleted_count;
    
    DELETE FROM option_iv_daily WHERE timestamp < v_cutoff_date;
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows from option_iv_daily', v_deleted_count;
    
    DELETE FROM iv_rank_daily WHERE timestamp < v_cutoff_date;
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows from iv_rank_daily', v_deleted_count;
    
    -- Очистка старых логов (старше 90 дней)
    DELETE FROM data_update_log WHERE start_time < NOW() - INTERVAL '90 days';
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows from data_update_log', v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- Статистика по таблицам (для мониторинга)
CREATE OR REPLACE VIEW table_statistics AS
SELECT 
    'perpetual_ohlcv' AS table_name,
    COUNT(*) AS total_rows,
    MIN(timestamp) AS earliest_date,
    MAX(timestamp) AS latest_date,
    COUNT(DISTINCT symbol) AS unique_symbols
FROM perpetual_ohlcv
UNION ALL
SELECT 
    'option_iv_daily',
    COUNT(*),
    MIN(timestamp),
    MAX(timestamp),
    COUNT(DISTINCT symbol)
FROM option_iv_daily
UNION ALL
SELECT 
    'iv_rank_daily',
    COUNT(*),
    MIN(timestamp),
    MAX(timestamp),
    COUNT(DISTINCT underlying)
FROM iv_rank_daily;

-- ============================================================================

COMMENT ON TABLE perpetual_ohlcv IS 'Исторические OHLCV данные бессрочных фьючерсов (daily timeframe)';
COMMENT ON TABLE option_iv_daily IS 'Ежедневные снапшоты IV и Greeks для опционов (~30 days to expiry)';
COMMENT ON TABLE iv_rank_daily IS 'Рассчитанные значения IV Rank (30-day rolling window)';
COMMENT ON TABLE data_update_log IS 'Логи выполнения задач обновления данных';
COMMENT ON TABLE system_config IS 'Системные конфигурации и метаданные';

-- ============================================================================
-- Завершение создания схемы
-- ============================================================================

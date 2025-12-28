// frontend/src/types/ivrank.types.ts

/**
 * Single IV Rank data point from the API
 */
export interface IVRankDataPoint {
  timestamp: string;        // ISO 8601 format: "2024-12-24T00:00:00Z"
  iv_rank: number;          // 0-100 percentile
  current_iv: number;       // Current implied volatility
  min_iv_30d: number;       // Minimum IV in last 30 days
  max_iv_30d: number;       // Maximum IV in last 30 days
}

/**
 * Response from GET /api/v1/iv-rank
 */
export interface IVRankResponse {
  base_coin: string;                    // "BTC", "ETH", etc.
  iv_rank_data: IVRankDataPoint[];      // Array of historical data points
}

/**
 * Single OHLCV candle data point
 */
export interface OHLCVDataPoint {
  timestamp: string;        // ISO 8601 format
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * Response from GET /api/v1/price-history
 */
export interface PriceHistoryResponse {
  symbol: string;                       // "BTCUSDT"
  candles: OHLCVDataPoint[];            // ← БЫЛО: price_data, СТАЛО: candles
}

/**
 * Transformed data for TradingView Lightweight Charts (Candlestick)
 */
export interface CandlestickData {
  time: number;             // Unix timestamp in seconds
  open: number;
  high: number;
  low: number;
  close: number;
}

/**
 * Transformed data for TradingView Lightweight Charts (Line)
 */
export interface LineData {
  time: number;             // Unix timestamp in seconds
  value: number;            // IV Rank (0-100)
}
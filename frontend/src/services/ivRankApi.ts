// frontend/src/services/ivRankApi.ts

import type { 
  IVRankResponse, 
  PriceHistoryResponse,
  CandlestickData,
  LineData 
} from '../types/ivrank.types';

const API_BASE_URL = '/api/v1';  // Relative URL - пройдёт через Vite proxy

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public endpoint?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Fetch IV Rank data from backend
 * @param baseCoin - Base coin symbol (e.g., "BTC", "ETH")
 * @param days - Number of days of historical data (minimum: 30, default: 365)
 * @returns Promise with IV Rank response
 */
export async function fetchIVRankData(
  baseCoin: string = 'BTC',
  days: number = 365
): Promise<IVRankResponse> {
  const endpoint = `${API_BASE_URL}/iv-rank?base_coin=${baseCoin}&days=${days}`;
 
  
  try {
    const response = await fetch(endpoint);
    
    if (!response.ok) {
      throw new APIError(
        `Failed to fetch IV Rank data: ${response.statusText}`,
        response.status,
        endpoint
      );
    }
    
    const data: IVRankResponse = await response.json();
    
    // Validate response structure
    if (!data.iv_rank_data || !Array.isArray(data.iv_rank_data)) {
      throw new APIError(
        'Invalid response structure: missing iv_rank_data array',
        undefined,
        endpoint
      );
    }
    
    return data;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    // Network error or other issues
    throw new APIError(
      `Network error while fetching IV Rank data: ${error}`,
      undefined,
      endpoint
    );
  }
}

/**
 * Fetch price history (OHLCV) data from backend
 * @param symbol - Trading symbol (e.g., "BTCUSDT")
 * @param days - Number of days of historical data (minimum: 30, default: 365)
 * @returns Promise with price history response
 */
export async function fetchPriceHistory(
  symbol: string = 'BTCUSDT',
  days: number = 365
): Promise<PriceHistoryResponse> {
  const endpoint = `${API_BASE_URL}/price-history?symbol=${symbol}&days=${days}`;
  
  try {
    const response = await fetch(endpoint);
    
    if (!response.ok) {
      throw new APIError(
        `Failed to fetch price history: ${response.statusText}`,
        response.status,
        endpoint
      );
    }
    
    const data: PriceHistoryResponse = await response.json();
    
    // Validate response structure
if (!data.candles || !Array.isArray(data.candles)) {  // ← БЫЛО: price_data, СТАЛО: candles
  throw new APIError(
    'Invalid response structure: missing candles array',  // ← обнови сообщение
    undefined,
    endpoint
  );
}
    
    return data;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    throw new APIError(
      `Network error while fetching price history: ${error}`,
      undefined,
      endpoint
    );
  }
}

/**
 * Transform OHLCV data to TradingView Candlestick format
 * @param candles - Array of OHLCV data points  // ← обнови комментарий
 * @returns Array of candlestick data for TradingView
 */
export function transformToCandlestickData(
  candles: PriceHistoryResponse['candles']  // ← БЫЛО: priceData и price_data
): CandlestickData[] {
  return candles.map(candle => ({  // ← БЫЛО: priceData
    time: Math.floor(new Date(candle.timestamp).getTime() / 1000),
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  }));
}

/**
 * Transform IV Rank data to TradingView Line format
 * @param ivRankData - Array of IV Rank data points
 * @returns Array of line data for TradingView
 */
export function transformToLineData(
  ivRankData: IVRankResponse['iv_rank_data']
): LineData[] {
  return ivRankData.map(point => ({
    time: Math.floor(new Date(point.timestamp).getTime() / 1000), // Convert to Unix timestamp (seconds)
    value: point.iv_rank,
  }));
}
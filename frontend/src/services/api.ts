import {
  OptionsBoardResponse,
  PayoffChartResponse,
  TradeEntry,
  PositionModel,
  PortfolioRiskModel,
  OptionsFilter,
  ApiResponse,
  PriceHistoryResponse,
  IVHistoryResponse,
  IVRankHistoryResponse,
} from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api/v1';

// Cache configuration
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private defaultCacheTTL = 60 * 1000; // 1 minute default cache TTL
  private maxRetries = 3;
  private retryDelay = 1000; // 1 second

  private async requestWithRetry(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<Response> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, options);
      
      // Retry on 5xx errors or network errors
      if (response.status >= 500 && retryCount < this.maxRetries) {
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, retryCount)));
        return this.requestWithRetry(endpoint, options, retryCount + 1);
      }
      
      return response;
    } catch (error) {
      // Retry on network errors
      if (retryCount < this.maxRetries) {
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, retryCount)));
        return this.requestWithRetry(endpoint, options, retryCount + 1);
      }
      throw error;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    cacheKey?: string,
    cacheTTL?: number
  ): Promise<ApiResponse<T>> {
    // Check cache if cacheKey is provided
    if (cacheKey && (!options.method || options.method === 'GET')) {
      const cached = this.getFromCache<T>(cacheKey);
      if (cached) {
        return {
          success: true,
          data: cached,
          timestamp: new Date().toISOString(),
        };
      }
    }
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    try {
      const response = await this.requestWithRetry(endpoint, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // Ignore JSON parsing errors
        }
        throw new ApiError(errorMessage, response.status);
      }
      
      const data = await response.json();
      
      // Cache the response if cacheKey is provided
      if (cacheKey && (!options.method || options.method === 'GET')) {
        this.setCache(cacheKey, data, cacheTTL || this.defaultCacheTTL);
      }
      
      return {
        success: true,
        data,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error'
      );
    }
  }

  private getFromCache<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  private setCache<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
    });
  }

  private clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  private generateCacheKey(endpoint: string, params?: any): string {
    const paramsStr = params ? JSON.stringify(params) : '';
    return `${endpoint}:${paramsStr}`;
  }

  // Options Board
  async getOptionsBoard(filters: OptionsFilter = {}): Promise<ApiResponse<OptionsBoardResponse>> {
    const params = new URLSearchParams();
    if (filters.base_coin) params.append('base_coin', filters.base_coin);
    if (filters.expiry) params.append('expiry', filters.expiry);
    if (filters.option_type) params.append('option_type', filters.option_type);
    if (filters.min_strike) params.append('min_strike', filters.min_strike.toString());
    if (filters.max_strike) params.append('max_strike', filters.max_strike.toString());
    
    const query = params.toString();
    const endpoint = `/options-board${query ? `?${query}` : ''}`;
    const cacheKey = this.generateCacheKey('options-board', filters);
    return this.request<OptionsBoardResponse>(endpoint, {}, cacheKey, 30 * 1000); // 30 seconds cache
  }

  // Portfolio Data
  async getPortfolio(): Promise<ApiResponse<PortfolioRiskModel>> {
    const endpoint = '/risk/portfolio';
    const cacheKey = this.generateCacheKey('portfolio');
    return this.request<PortfolioRiskModel>(endpoint, {}, cacheKey, 10 * 1000); // 10 seconds cache
  }

  async getPositions(): Promise<ApiResponse<PositionModel[]>> {
    const endpoint = '/positions';
    const cacheKey = this.generateCacheKey('positions');
    return this.request<PositionModel[]>(endpoint, {}, cacheKey, 10 * 1000);
  }

  // Payoff Chart - TEMPORARILY DISABLED (endpoint not implemented in backend)
  async getPayoffChart(): Promise<ApiResponse<PayoffChartResponse>> {
    // TODO: Implement backend endpoint for payoff chart
    // For now, return mock data or throw error
    throw new ApiError('Payoff chart endpoint not implemented in backend');
    
    // Uncomment when backend endpoint is available:
    // const params = new URLSearchParams();
    // if (daysToExpiry) params.append('days_to_expiry', daysToExpiry.toString());
    // if (priceRangePct) params.append('price_range_pct', priceRangePct.toString());
    //
    // const query = params.toString();
    // const endpoint = `/payoff-chart${query ? `?${query}` : ''}`;
    // const cacheKey = this.generateCacheKey('payoff-chart', { daysToExpiry, priceRangePct });
    // return this.request<PayoffChartResponse>(endpoint, {}, cacheKey, 30 * 1000);
  }

  // Trade Log - TEMPORARILY DISABLED (endpoint not implemented in backend)
  async getTradeLog(): Promise<ApiResponse<TradeEntry[]>> {
    // TODO: Implement backend endpoint for trade log
    // For now, return mock data or throw error
    throw new ApiError('Trade log endpoint not implemented in backend');
    
    // Uncomment when backend endpoint is available:
    // const params = new URLSearchParams();
    // if (filters.start_date) params.append('start_date', filters.start_date);
    // if (filters.end_date) params.append('end_date', filters.end_date);
    // if (filters.symbol) params.append('symbol', filters.symbol);
    // if (filters.side) params.append('side', filters.side);
    // if (filters.limit) params.append('limit', filters.limit.toString());
    // if (filters.offset) params.append('offset', filters.offset.toString());
    //
    // const query = params.toString();
    // const endpoint = `/trade-log${query ? `?${query}` : ''}`;
    // const cacheKey = this.generateCacheKey('trade-log', filters);
    // return this.request<TradeEntry[]>(endpoint, {}, cacheKey, 60 * 1000); // 1 minute cache
  }

  // Metrics - TEMPORARILY DISABLED (endpoint not implemented in backend)
  async getMetrics(): Promise<ApiResponse<any>> {
    // TODO: Implement backend endpoint for greeks summary
    throw new ApiError('Metrics endpoint not implemented in backend');
    
    // Uncomment when backend endpoint is available:
    // const endpoint = '/greeks/summary';
    // const cacheKey = this.generateCacheKey('metrics');
    // return this.request<any>(endpoint, {}, cacheKey, 5 * 1000); // 5 seconds cache
  }

  // Margin info
  async getMargin(): Promise<ApiResponse<any>> {
    const endpoint = '/margin';
    const cacheKey = this.generateCacheKey('margin');
    return this.request<any>(endpoint, {}, cacheKey, 10 * 1000);
  }

  // Coin risk
  async getCoinRisk(coin: string): Promise<ApiResponse<any>> {
    const endpoint = `/risk/coin/${coin}`;
    const cacheKey = this.generateCacheKey(`coin-risk-${coin}`);
    return this.request<any>(endpoint, {}, cacheKey, 10 * 1000);
  }

  // Get supported coins
  async getCoins(): Promise<ApiResponse<string[]>> {
    const endpoint = '/coins';
    const cacheKey = this.generateCacheKey('coins');
    return this.request<string[]>(endpoint, {}, cacheKey, 300 * 1000); // 5 minutes cache
  }

  // Price history
  async getPriceHistory(
    symbol: string = 'BTCUSDT', // Changed from 'BTC-PERPETUAL' to match backend
    days: number = 365 // Changed from 1825 to match backend default
  ): Promise<ApiResponse<PriceHistoryResponse>> {
    const params = new URLSearchParams();
    params.append('symbol', symbol);
    params.append('days', days.toString());
    const query = params.toString();
    const endpoint = `/price-history${query ? `?${query}` : ''}`;
    const cacheKey = this.generateCacheKey('price-history', { symbol, days });
    return this.request<PriceHistoryResponse>(endpoint, {}, cacheKey, 300 * 1000); // 5 minutes cache
  }

  // IV history - TEMPORARILY DISABLED (use IV Rank instead)
  async getIVHistory(): Promise<ApiResponse<IVHistoryResponse>> {
    // TODO: Implement backend endpoint for IV history or use IV Rank
    throw new ApiError('IV history endpoint not implemented. Use getIVRank() instead.');
    
    // Uncomment when backend endpoint is available:
    // const params = new URLSearchParams();
    // params.append('base_coin', baseCoin);
    // params.append('period', period.toString());
    // const query = params.toString();
    // const endpoint = `/iv-history${query ? `?${query}` : ''}`;
    // const cacheKey = this.generateCacheKey('iv-history', { baseCoin, period });
    // return this.request<IVHistoryResponse>(endpoint, {}, cacheKey, 300 * 1000); // 5 minutes cache
  }

  // IV Rank history
  async getIVRank(
    baseCoin: string = 'BTC',
    days: number = 365 // Changed from 30 to match backend default
  ): Promise<ApiResponse<IVRankHistoryResponse>> {
    const params = new URLSearchParams();
    params.append('base_coin', baseCoin);
    params.append('days', days.toString());
    const query = params.toString();
    const endpoint = `/iv-rank${query ? `?${query}` : ''}`;
    const cacheKey = this.generateCacheKey('iv-rank', { baseCoin, days });
    return this.request<IVRankHistoryResponse>(endpoint, {}, cacheKey, 300 * 1000); // 5 minutes cache
  }

  // Export - TEMPORARILY DISABLED (endpoint not implemented in backend)
  async exportData(): Promise<Blob> {
    // TODO: Implement backend endpoint for export
    throw new ApiError('Export endpoint not implemented in backend');
    
    // Uncomment when backend endpoint is available:
    // const url = `${API_BASE_URL}/export?format=${format}`;
    // const response = await fetch(url);
    //
    // if (!response.ok) {
    //   throw new ApiError(`Export failed: HTTP ${response.status}`);
    // }
    //
    // return await response.blob();
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Clear cache for specific endpoint
  clearCacheFor(endpoint: string, params?: any): void {
    const cacheKey = this.generateCacheKey(endpoint, params);
    this.clearCache(cacheKey);
  }

  // Clear all cache
  clearAllCache(): void {
    this.clearCache();
  }
}


// Всегда использовать реальный API клиент
const apiClient = new ApiClient();
export default apiClient;
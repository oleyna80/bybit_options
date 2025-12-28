/**
 * TypeScript типы для веб-интерфейса анализа опционного портфеля Bybit
 * Основаны на Pydantic моделях из backend/data_models.py
 */

// Enums
export enum PositionSide {
  BUY = "Buy",
  SELL = "Sell"
}

export enum PositionType {
  LINEAR = "LINEAR",
  OPTION = "OPTION",
  INVERSE = "INVERSE"
}

export enum OptionType {
  CALL = "C",
  PUT = "P"
}

// Basic models
export interface CoinHolding {
  coin: string;
  wallet_balance: number;
  usd_value: number;
  equity: number;
  unrealized_pnl: number;
}

export interface GreeksModel {
  delta_coin: number;
  gamma_coin: number;
  vega_usd: number;
  theta_usd: number;
}

export interface SlippageMetrics {
  bid: number;
  ask: number;
  mark_price: number;
  spread_abs: number;
  spread_pct: number;
  mid_price: number;
  slippage_risk: "LOW" | "MEDIUM" | "HIGH";
}

export interface IVMetrics {
  position_iv: number | null;
  atm_iv: number | null;
  iv_diff_pct: number | null;
  is_expensive: boolean | null;
}

export interface GammaRentMetrics {
  theta_usd: number;
  gamma_coin: number;
  gamma_rent: number | null;
  gamma_rent_normalized: number | null;
  interpretation: string;
}

export interface PositionModel {
  symbol: string;
  side: PositionSide;
  size: number;
  pos_type: PositionType;
  base_coin: string;
  
  // Option-specific fields
  series: string | null;
  option_type: OptionType | null;
  strike: number | null;
  
  // Greeks
  greeks: GreeksModel;
  
  // Risk metrics
  slippage: SlippageMetrics | null;
  iv_metrics: IVMetrics | null;
  gamma_rent: GammaRentMetrics | null;
  
  // Position value
  entry_price: number | null;
  mark_value: number | null;
  unrealized_pnl: number | null;
}

export interface CoinRiskModel {
  base_coin: string;
  total_greeks: GreeksModel;
  futures_greeks: GreeksModel;
  options_greeks: GreeksModel;
  series_greeks: Record<string, GreeksModel>;
  underlying_price: number | null;
  positions: PositionModel[];
}

export interface MarginModel {
  account_type: string;
  total_equity: number;
  available_balance: number;
  used_margin: number;
  initial_margin: number;
  maintenance_margin: number;
  margin_ratio: number | null;
  unrealized_pnl: number;
  realized_pnl: number;
  holdings: CoinHolding[];
  health_status: "HEALTHY" | "MODERATE" | "HIGH_RISK" | "UNKNOWN";
}

export interface PortfolioRiskModel {
  timestamp: string;
  margin: MarginModel;
  coin_risks: Record<string, CoinRiskModel>;
  total_vega_usd: number;
  total_theta_usd: number;
  warnings: string[];
}

// Frontend-specific types
export interface OptionRow {
  // Basic option info
  symbol: string;
  clean_symbol: string;
  base_coin: string;
  expiry: string;
  strike: number;
  type: string;
  type_code: string;
  moneyness: string;
  
  // Prices
  prices: {
    mark: number;
    bid: number;
    ask: number;
    last: number;
    underlying: number;
  };
  
  // Spread
  spread: {
    absolute: number;
    percent: number;
  };
  
  // Implied volatility
  iv: {
    bid: number;
    mark: number;
    ask: number;
  };
  
  // Greeks
  greeks: {
    delta: number;
    gamma: number;
    vega: number;
    theta: number;
  };
  
  // Liquidity
  liquidity: {
    bid_size: number;
    ask_size: number;
    open_interest: number;
    volume_24h: number;
    turnover_24h: number;
  };
  
  // Value analysis
  value_analysis: {
    intrinsic: number;
    extrinsic: number;
    extrinsic_percent: number;
  };
  
  // Portfolio info (optional)
  is_in_portfolio?: boolean;
  position_size?: number;
}

export interface PortfolioMetrics {
  total_delta: number;
  total_gamma: number;
  total_vega: number;
  total_theta: number;
  total_equity: number;
  margin_utilization: number;
  unrealized_pnl: number;
  realized_pnl: number;
}

export interface TradeEntry {
  timestamp: string;
  symbol: string;
  side: PositionSide;
  size: number;
  price: number;
  fee: number;
  role: "Taker" | "Maker";
  iv: number | null;
  pnl: number | null;
}

export interface PayoffChartData {
  current_price: number;
  price_range: number[];
  pnl: number[];
  breakeven_points: number[];
  max_profit: number;
  max_loss: number;
}

export interface WebSocketMessage {
  type: "portfolio_update" | "options_board_update" | "trade_update" | "error" | "connection_established" | "subscription_updated" | "pong";
  timestamp: string;
  data: PortfolioRiskModel | OptionRow[] | TradeEntry[] | string | any;
}

// Filter types
export interface OptionsFilter {
  base_coin?: string;
  expiry?: string;
  option_type?: OptionType;
  min_strike?: number;
  max_strike?: number;
}

export interface TradeLogFilter {
  start_date?: string;
  end_date?: string;
  symbol?: string;
  side?: PositionSide;
  limit?: number;
  offset?: number;
}

// Store types
export interface PortfolioStoreState {
  // State
  positions: PositionModel[];
  optionsBoard: OptionRow[];
  portfolioMetrics: PortfolioMetrics;
  tradeLog: TradeEntry[];
  portfolioRisk: PortfolioRiskModel | null;
  
  // UI state
  selectedExpiry: string;
  selectedBaseCoin: string;
  isLoading: boolean;
  error: string | null;
  
  // WebSocket
  wsConnected: boolean;
  lastUpdate: string | null;
  
  // Actions (will be defined in store)
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: string;
}

export interface OptionsBoardResponse {
  underlying_price: number;
  expiry: string;
  options: OptionRow[];
}

export interface PayoffChartResponse {
  current_price: number;
  price_range: number[];
  pnl: number[];
  breakeven_points: number[];
  max_profit: number;
  max_loss: number;
}

export interface ExportData {
  metadata: {
    timestamp: string;
    underlying_symbol: string;
    underlying_price: number;
    expiry: string;
    days_to_expiry: number;
    atm_strike: number;
    atm_iv: number;
  };
  options: OptionRow[];
  portfolio_positions: PositionModel[];
  ai_summary: string;
}

// Historical data types
export interface PerpetualOHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OptionIVDaily {
  timestamp: string;
  atm_strike: number;
  iv_value: number;
  days_to_expiry: number;
}

export interface IVRankDaily {
  timestamp: string;
  iv_rank: number;
  current_iv: number;
  min_iv_30d: number;
  max_iv_30d: number;
}

// Historical response types
export interface PriceHistoryResponse {
  symbol: string;
  candles: PerpetualOHLCV[];
}

export interface IVHistoryResponse {
  base_coin: string;
  iv_data: OptionIVDaily[];
}

export interface IVRankHistoryResponse {
  base_coin: string;
  iv_rank_data: IVRankDaily[];
}
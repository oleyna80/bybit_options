/**
 * AMM (Automated Market Maker) Type Definitions
 */

export interface AmmStrategy {
  id: number;
  name: string;
  symbol: string;
  status: 'ACTIVE' | 'PAUSED';
  skew_factor: number;
  spread_bps: number;
  min_iv: number;
  max_iv: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioGreeksData {
  delta: number;
  gamma: number;
  vega: number;
  theta: number;
  timestamp: string;
}

export interface RiskDecision {
  id: number;
  timestamp: string;
  decision_type: 'PORTFOLIO_GATE' | 'LEG_GATE';
  approved: boolean;
  reason: string;
  strategy_id?: number;
  leg_details?: string;
}

export interface EngineStatus {
  is_running: boolean;
  last_cycle_at?: string;
  mode: 'MANUAL' | 'AUTO';
}

export interface AgentCommand {
  command_type: 'UPDATE_STRATEGY_PARAMS' | 'PAUSE_STRATEGY' | 'RESUME_STRATEGY';
  strategy_id?: number;
  params?: {
    skew_factor?: number;
    spread_bps?: number;
    min_iv?: number;
    max_iv?: number;
  };
}

export interface CreateStrategyRequest {
  name: string;
  symbol: string;
  skew_factor?: number;
  spread_bps?: number;
  min_iv?: number;
  max_iv?: number;
}

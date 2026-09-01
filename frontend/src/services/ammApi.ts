/**
 * AMM API Service
 * Handles all API calls for AMM Dashboard
 */

import apiClient from './api';
import type {
    AmmStrategy,
    PortfolioGreeksData,
    RiskDecision,
    EngineStatus,
    AgentCommand,
    CreateStrategyRequest,
} from '../types/amm';

export const ammApi = {
    // ==================== Strategies ====================

    /**
     * Fetch all AMM strategies
     */
    getStrategies: async (): Promise<{ strategies: AmmStrategy[] }> => {
        const response = await apiClient['request']<{ strategies: AmmStrategy[] }>('/amm/strategies');
        return response.data;
    },

    /**
     * Create a new AMM strategy
     */
    createStrategy: async (data: CreateStrategyRequest): Promise<AmmStrategy> => {
        const response = await apiClient['request']<AmmStrategy>('/amm/strategies', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        return response.data;
    },

    // ==================== Portfolio Greeks ====================

    /**
     * Get aggregated portfolio Greeks
     */
    getPortfolioGreeks: async (): Promise<PortfolioGreeksData> => {
        const response = await apiClient['request']<PortfolioGreeksData>('/amm/portfolio/greeks');
        return response.data;
    },

    // ==================== Risk Decisions ====================

    /**
     * Fetch recent risk decisions
     */
    getRiskDecisions: async (limit = 50): Promise<{ decisions: RiskDecision[] }> => {
        const response = await apiClient['request']<{ decisions: RiskDecision[] }>(
            `/amm/risk/decisions?limit=${limit}`
        );
        return response.data;
    },

    // ==================== Engine Control ====================

    /**
     * Get current engine status
     */
    getEngineStatus: async (): Promise<EngineStatus> => {
        const response = await apiClient['request']<EngineStatus>('/amm/status');
        return response.data;
    },

    /**
     * Start the AMM engine
     */
    startEngine: async (): Promise<{ message: string }> => {
        const response = await apiClient['request']<{ message: string }>('/amm/engine/start', {
            method: 'POST',
        });
        return response.data;
    },

    /**
     * Stop the AMM engine
     */
    stopEngine: async (): Promise<{ message: string }> => {
        const response = await apiClient['request']<{ message: string }>('/amm/engine/stop', {
            method: 'POST',
        });
        return response.data;
    },

    // ==================== Operating Mode ====================

    /**
     * Get current operating mode
     */
    getMode: async (): Promise<{ mode: 'MANUAL' | 'AUTO' }> => {
        const response = await apiClient['request']<{ mode: 'MANUAL' | 'AUTO' }>('/amm/mode');
        return response.data;
    },

    /**
     * Set operating mode
     */
    setMode: async (mode: 'MANUAL' | 'AUTO'): Promise<{ message: string }> => {
        const response = await apiClient['request']<{ message: string }>('/amm/mode', {
            method: 'POST',
            body: JSON.stringify({ mode }),
        });
        return response.data;
    },

    // ==================== Agent Commands ====================

    /**
     * Send command to Trading Expert agent
     */
    sendAgentCommand: async (command: AgentCommand): Promise<{ message: string }> => {
        const response = await apiClient['request']<{ message: string }>('/amm/agent/command', {
            method: 'POST',
            body: JSON.stringify(command),
        });
        return response.data;
    },

    /**
     * Pause a strategy
     */
    pauseStrategy: async (strategyId: number): Promise<{ message: string }> => {
        return ammApi.sendAgentCommand({
            command_type: 'PAUSE_STRATEGY',
            strategy_id: strategyId,
        });
    },

    /**
     * Resume a strategy
     */
    resumeStrategy: async (strategyId: number): Promise<{ message: string }> => {
        return ammApi.sendAgentCommand({
            command_type: 'RESUME_STRATEGY',
            strategy_id: strategyId,
        });
    },

    /**
     * Update strategy parameters
     */
    updateStrategyParams: async (
        strategyId: number,
        params: {
            skew_factor?: number;
            spread_bps?: number;
            min_iv?: number;
            max_iv?: number;
        }
    ): Promise<{ message: string }> => {
        return ammApi.sendAgentCommand({
            command_type: 'UPDATE_STRATEGY_PARAMS',
            strategy_id: strategyId,
            params,
        });
    },
};

export default ammApi;

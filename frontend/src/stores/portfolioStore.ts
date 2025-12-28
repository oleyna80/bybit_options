import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  PortfolioStoreState,
  PositionModel,
  OptionRow,
  TradeEntry,
  PortfolioMetrics,
  PortfolioRiskModel,
  OptionsFilter,
  WebSocketMessage,
  PositionSide,
  PositionType,
  OptionType,
} from '../types';
import apiClient from '../services/api';
import wsClient from '../services/websocket';

interface PortfolioStoreActions {
  // Data fetching
  fetchOptionsBoard: (filters: OptionsFilter) => Promise<void>;
  fetchPortfolio: () => Promise<void>;
  fetchTradeLog: () => Promise<void>;
  
  // WebSocket
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  
  // UI actions
  setSelectedExpiry: (expiry: string) => void;
  setSelectedBaseCoin: (coin: string) => void;
  exportData: (format: 'json' | 'md') => void;
  
  // Mock data for development
  loadMockData: () => void;
}

const initialMetrics: PortfolioMetrics = {
  total_delta: 0.5234,
  total_gamma: 0.00123,
  total_vega: 4567.89,
  total_theta: -123.45,
  total_equity: 52345.67,
  margin_utilization: 45.5,
  unrealized_pnl: 557.95,
  realized_pnl: 1234.56,
};

const initialState: PortfolioStoreState = {
  // State
  positions: [],
  optionsBoard: [],
  portfolioMetrics: initialMetrics,
  tradeLog: [],
  portfolioRisk: null,
  
  // UI state
  selectedExpiry: '19DEC25',
  selectedBaseCoin: 'BTC',
  isLoading: false,
  error: null,
  
  // WebSocket
  wsConnected: false,
  lastUpdate: null,
};

export const usePortfolioStore = create<PortfolioStoreState & PortfolioStoreActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        fetchOptionsBoard: async (filters: OptionsFilter) => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiClient.getOptionsBoard(filters);
            
            if (response.success) {
              set({
                optionsBoard: response.data.options,
                isLoading: false,
                lastUpdate: new Date().toISOString(),
              });
            } else {
              throw new Error(response.error || 'Failed to fetch options board');
            }
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch options board',
              isLoading: false,
            });
          }
        },
        
        fetchPortfolio: async () => {
          set({ isLoading: true, error: null });
          try {
            const [portfolioResponse, positionsResponse] = await Promise.all([
              apiClient.getPortfolio(),
              apiClient.getPositions(),
            ]);
            
            if (portfolioResponse.success && positionsResponse.success) {
              const portfolioRisk = portfolioResponse.data;
              const positions = positionsResponse.data;
              
              // Update portfolio metrics from portfolio risk
              const portfolioMetrics: PortfolioMetrics = {
                total_delta: Object.values(portfolioRisk.coin_risks).reduce(
                  (sum, coinRisk) => sum + coinRisk.total_greeks.delta_coin, 0
                ),
                total_gamma: Object.values(portfolioRisk.coin_risks).reduce(
                  (sum, coinRisk) => sum + coinRisk.total_greeks.gamma_coin, 0
                ),
                total_vega: portfolioRisk.total_vega_usd,
                total_theta: portfolioRisk.total_theta_usd,
                total_equity: portfolioRisk.margin.total_equity,
                margin_utilization: portfolioRisk.margin.margin_ratio || 0,
                unrealized_pnl: portfolioRisk.margin.unrealized_pnl,
                realized_pnl: portfolioRisk.margin.realized_pnl,
              };
              
              set({
                positions,
                portfolioRisk,
                portfolioMetrics,
                isLoading: false,
                lastUpdate: new Date().toISOString(),
              });
            } else {
              throw new Error('Failed to fetch portfolio data');
            }
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch portfolio',
              isLoading: false,
            });
          }
        },
        
        fetchTradeLog: async () => {
          set({ isLoading: true, error: null });
          try {
            // Trade log endpoint is not implemented in backend yet
            // For now, use mock data or empty array
            console.warn('Trade log endpoint not implemented, using mock data');
            
            // Return empty array for now
            set({
              tradeLog: [],
              isLoading: false,
              lastUpdate: new Date().toISOString(),
            });
            
            // Uncomment when backend endpoint is available:
            // const response = await apiClient.getTradeLog(filters);
            //
            // if (response.success) {
            //   set({
            //     tradeLog: response.data,
            //     isLoading: false,
            //     lastUpdate: new Date().toISOString(),
            //   });
            // } else {
            //   throw new Error(response.error || 'Failed to fetch trade log');
            // }
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch trade log',
              isLoading: false,
            });
          }
        },
        
        connectWebSocket: () => {
          const currentState = get();
          
          if (currentState.wsConnected) {
            console.log('WebSocket already connected');
            return;
          }
          
          // Connect to WebSocket
          wsClient.connect();
          
          // Subscribe to WebSocket messages
          const unsubscribe = wsClient.subscribe((message: WebSocketMessage) => {
            get().handleWebSocketMessage(message);
          });
          
          // Subscribe to status changes
          const statusUnsubscribe = wsClient.onStatusChange((connected: boolean) => {
            set({ wsConnected: connected });
          });
          
          // Store unsubscribe functions
          (window as any).__wsUnsubscribe = unsubscribe;
          (window as any).__wsStatusUnsubscribe = statusUnsubscribe;
          
          set({ wsConnected: wsClient.isConnected() });
        },
        
        disconnectWebSocket: () => {
          const unsubscribe = (window as any).__wsUnsubscribe;
          const statusUnsubscribe = (window as any).__wsStatusUnsubscribe;
          
          if (unsubscribe) {
            unsubscribe();
          }
          if (statusUnsubscribe) {
            statusUnsubscribe();
          }
          
          wsClient.disconnect();
          set({ wsConnected: false });
        },
        
        handleWebSocketMessage: (message: WebSocketMessage) => {
          try {
            switch (message.type) {
              case 'portfolio_update':
                const portfolioRisk = message.data as PortfolioRiskModel;
                
                // Update portfolio metrics from portfolio risk
                const portfolioMetrics: PortfolioMetrics = {
                  total_delta: Object.values(portfolioRisk.coin_risks).reduce(
                    (sum, coinRisk) => sum + coinRisk.total_greeks.delta_coin, 0
                  ),
                  total_gamma: Object.values(portfolioRisk.coin_risks).reduce(
                    (sum, coinRisk) => sum + coinRisk.total_greeks.gamma_coin, 0
                  ),
                  total_vega: portfolioRisk.total_vega_usd,
                  total_theta: portfolioRisk.total_theta_usd,
                  total_equity: portfolioRisk.margin.total_equity,
                  margin_utilization: portfolioRisk.margin.margin_ratio || 0,
                  unrealized_pnl: portfolioRisk.margin.unrealized_pnl,
                  realized_pnl: portfolioRisk.margin.realized_pnl,
                };
                
                set({
                  portfolioRisk,
                  portfolioMetrics,
                  lastUpdate: message.timestamp,
                });
                break;
                
              case 'options_board_update':
                const optionsData = message.data as OptionRow[];
                set({
                  optionsBoard: optionsData,
                  lastUpdate: message.timestamp,
                });
                break;
                
              case 'trade_update':
                const tradeData = message.data as TradeEntry[];
                set({
                  tradeLog: [...tradeData, ...get().tradeLog].slice(0, 100), // Keep last 100 trades
                  lastUpdate: message.timestamp,
                });
                break;
                
              case 'connection_established':
                console.log('WebSocket connection established:', message.data);
                break;
                
              case 'subscription_updated':
                console.log('WebSocket subscriptions updated:', message.data);
                break;
                
              case 'error':
                console.error('WebSocket error:', message.data);
                set({ error: typeof message.data === 'string' ? message.data : JSON.stringify(message.data) });
                break;
                
              default:
                console.log('Unhandled WebSocket message type:', message.type, message.data);
            }
          } catch (error) {
            console.error('Error handling WebSocket message:', error, message);
          }
        },
        
        setSelectedExpiry: (expiry: string) => {
          set({ selectedExpiry: expiry });
        },
        
        setSelectedBaseCoin: (coin: string) => {
          set({ selectedBaseCoin: coin });
        },
        
        exportData: async (format: 'json' | 'md' | 'csv') => {
          const store = get();
          
          try {
            // Export endpoint is not implemented in backend yet
            // Use local export instead
            console.warn('Export endpoint not implemented, using local export');
            
            const exportData = {
              metadata: {
                timestamp: new Date().toISOString(),
                underlying_symbol: 'BTCUSDT',
                underlying_price: 95000.50,
                expiry: store.selectedExpiry,
                days_to_expiry: 7,
                atm_strike: 95000,
                atm_iv: 0.65,
              },
              options: store.optionsBoard,
              portfolio_positions: store.positions,
              portfolio_metrics: store.portfolioMetrics,
              ai_summary: `Portfolio is ${store.portfolioMetrics.total_delta >= 0 ? 'delta positive' : 'delta negative'} with ${store.portfolioMetrics.total_theta >= 0 ? 'positive' : 'negative'} theta.`,
            };
            
            let content: string;
            let mimeType: string;
            let extension: string;
            
            if (format === 'json') {
              content = JSON.stringify(exportData, null, 2);
              mimeType = 'application/json';
              extension = 'json';
            } else if (format === 'md') {
              content = `# Portfolio Export
**Timestamp:** ${exportData.metadata.timestamp}
**Underlying:** ${exportData.metadata.underlying_symbol} @ $${exportData.metadata.underlying_price}
**Expiry:** ${exportData.metadata.expiry} (${exportData.metadata.days_to_expiry} days)

## Portfolio Metrics
- Total Delta: ${store.portfolioMetrics.total_delta.toFixed(4)}
- Total Gamma: ${store.portfolioMetrics.total_gamma.toFixed(6)}
- Total Vega: $${store.portfolioMetrics.total_vega.toFixed(2)}
- Total Theta: $${store.portfolioMetrics.total_theta.toFixed(2)}
- Total Equity: $${store.portfolioMetrics.total_equity.toFixed(2)}
- Margin Utilization: ${store.portfolioMetrics.margin_utilization.toFixed(1)}%

## Positions (${exportData.portfolio_positions.length})
${exportData.portfolio_positions.map(p => `- ${p.symbol}: ${p.size} @ $${p.entry_price} (P&L: $${p.unrealized_pnl?.toFixed(2) || '0.00'})`).join('\n')}

## AI Summary
${exportData.ai_summary}`;
              mimeType = 'text/markdown';
              extension = 'md';
            } else {
              // CSV fallback
              const headers = ['timestamp', 'symbol', 'side', 'size', 'price', 'pnl'];
              const rows = store.positions.map(p => [
                new Date().toISOString(),
                p.symbol,
                p.side,
                p.size,
                p.entry_price,
                p.unrealized_pnl
              ].join(','));
              content = [headers.join(','), ...rows].join('\n');
              mimeType = 'text/csv';
              extension = 'csv';
            }
            
            const dataBlob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `portfolio-export-${new Date().toISOString().split('T')[0]}.${extension}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            setTimeout(() => URL.revokeObjectURL(url), 100);
            
          } catch (error) {
            console.error('Export failed:', error);
            set({ error: error instanceof Error ? error.message : 'Export failed' });
          }
        },
        
        loadMockData: () => {
          // Load comprehensive mock data for development
          const mockOptions: OptionRow[] = [
            {
              symbol: 'BTC-19DEC25-90000-C',
              clean_symbol: 'BTC-19DEC25-90000-C',
              base_coin: 'BTC',
              expiry: '19DEC25',
              strike: 90000,
              type: 'Call',
              type_code: 'C',
              moneyness: 'ITM',
              prices: {
                mark: 1245.0,
                bid: 1234.5,
                ask: 1256.8,
                last: 1240.0,
                underlying: 95000.50,
              },
              spread: {
                absolute: 22.3,
                percent: 1.8,
              },
              iv: {
                bid: 0.64,
                mark: 0.65,
                ask: 0.66,
              },
              greeks: {
                delta: 0.75,
                gamma: 0.000045,
                vega: 234.56,
                theta: -45.67,
              },
              liquidity: {
                bid_size: 10,
                ask_size: 15,
                open_interest: 1500,
                volume_24h: 150,
                turnover_24h: 186750,
              },
              value_analysis: {
                intrinsic: 5000,
                extrinsic: 1245,
                extrinsic_percent: 100,
              },
            },
            // ... more options
          ];
          
          const mockPositions: PositionModel[] = [
            {
              symbol: 'BTC-19DEC25-100000-C-USDT',
              side: PositionSide.BUY,
              size: 1.5,
              pos_type: PositionType.OPTION,
              base_coin: 'BTC',
              series: '19DEC25',
              option_type: OptionType.CALL,
              strike: 100000,
              greeks: {
                delta_coin: 0.7523,
                gamma_coin: 0.000045,
                vega_usd: 234.56,
                theta_usd: -45.67,
              },
              slippage: null,
              iv_metrics: null,
              gamma_rent: null,
              entry_price: 1245.0,
              mark_value: 1300.5,
              unrealized_pnl: 83.25,
            },
            // ... more positions
          ];
          
          const mockTrades: TradeEntry[] = [
            {
              timestamp: '2025-12-18T10:30:00Z',
              symbol: 'BTC-19DEC25-100000-C-USDT',
              side: PositionSide.BUY,
              size: 1.5,
              price: 1245.0,
              fee: 1.87,
              role: 'Taker',
              iv: 0.65,
              pnl: 83.25,
            },
            // ... more trades
          ];
          
          set({
            optionsBoard: mockOptions,
            positions: mockPositions,
            tradeLog: mockTrades,
            wsConnected: true,
            lastUpdate: new Date().toISOString(),
          });
        },
      }),
      {
        name: 'portfolio-store',
        partialize: (state) => ({
          selectedExpiry: state.selectedExpiry,
          selectedBaseCoin: state.selectedBaseCoin,
        }),
      }
    )
  )
);
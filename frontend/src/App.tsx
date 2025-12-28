import React, { useEffect } from 'react';
import { usePortfolioStore } from './stores/portfolioStore';
import { OptionsBoard } from './components/OptionsBoard/OptionsBoard';
import PortfolioTableV2 from './components/Portfolio/PortfolioTableV2';
import { MetricsCards } from './components/Portfolio/MetricsCards';
import { PayoffChart } from './components/Charts/PayoffChart';
import { TradeLog } from './components/TradeLog/TradeLog';
import { LoadingSpinner } from './components/Common/LoadingSpinner';
import { ErrorMessage } from './components/Common/ErrorMessage';
import { BarChart3, Wallet, TrendingUp, Clock, Settings, Download } from 'lucide-react';
import apiClient from './services/api';
import websocketService from './services/websocket';
import { IVRankChart } from './components/Charts/IVRankChart';

const App: React.FC = () => {
  const {
    optionsBoard: options,
    positions,
    portfolioMetrics: metrics,
    isLoading: loading,
    error,
    selectedExpiry,
    fetchOptionsBoard,
    fetchPortfolio,
    fetchTradeLog,
    connectWebSocket,
    disconnectWebSocket,
  } = usePortfolioStore();

  // Initialize data on mount
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch all data in parallel using store methods
        await Promise.all([
          fetchOptionsBoard({ expiry: selectedExpiry, base_coin: 'BTC' }),
          fetchPortfolio(),
          fetchTradeLog(),
        ]);
      } catch (err) {
        console.error('Failed to fetch initial data:', err);
      }
    };

    fetchInitialData();
  }, [selectedExpiry, fetchOptionsBoard, fetchPortfolio, fetchTradeLog]);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  const handleExportJson = async () => {
    try {
      await apiClient.exportData();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleExportMarkdown = async () => {
    try {
      await apiClient.exportData();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading && options.length === 0 && positions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading portfolio data..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-8 w-8 text-blue-400" />
              <h1 className="text-2xl font-bold">Bybit Options Risk Engine</h1>
            </div>
            <div className="text-sm text-gray-400">
              Real-time portfolio analysis & risk management
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm">Live</span>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={handleExportJson}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-md text-sm font-medium flex items-center space-x-1 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export JSON</span>
              </button>
              <button
                onClick={handleExportMarkdown}
                className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-md text-sm font-medium flex items-center space-x-1 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export MD</span>
              </button>
              <button className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-md text-sm font-medium flex items-center space-x-1 transition-colors">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Metrics Cards Row */}
        <div className="mb-6">
          <MetricsCards />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Options Board */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-blue-400" />
                  <h2 className="text-xl font-semibold">Options Board</h2>
                </div>
                <div className="text-sm text-gray-400">
                  {options.length} options • {selectedExpiry === 'All' ? 'All expiries' : `Expiry: ${selectedExpiry}`}
                </div>
              </div>
              <OptionsBoard />
            </div>
          </div>

          {/* Right Column - Portfolio & Chart */}
          <div className="space-y-6">
            {/* Portfolio Table */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Wallet className="h-5 w-5 text-green-400" />
                  <h2 className="text-xl font-semibold">Portfolio Positions</h2>
                </div>
                <div className="text-sm text-gray-400">
                  {positions.length} positions • Total P&L: ${metrics.unrealized_pnl?.toFixed(2) || '0.00'}
                </div>
              </div>
              <PortfolioTableV2 />
            </div>

            {/* Payoff Chart */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  <h2 className="text-xl font-semibold">P&L at Expiry</h2>
                </div>
                <div className="text-sm text-gray-400">
                  {selectedExpiry === 'All' ? 'Select expiry to view chart' : `Expiry: ${selectedExpiry}`}
                </div>
              </div>
              <PayoffChart />
            </div>
          </div>
        </div>

        {/* IV Rank Analysis - Full Width */}
        <div className="mt-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <IVRankChart
              baseCoin="BTC"
              symbol="BTCUSDT"
              days={365}
              height="600px"
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between text-sm text-gray-400">
          <div>
            <span className="font-medium">Bybit Options Risk Engine</span> • v1.0.0 • Data updates via WebSocket
          </div>
          <div className="flex space-x-4">
            <span>Connected: {websocketService.isConnected() ? '✓' : '✗'}</span>
            <span>Last update: {new Date().toLocaleTimeString()}</span>
            <button
              onClick={() => websocketService.connect()}
              className="text-blue-400 hover:text-blue-300"
            >
              Reconnect
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;

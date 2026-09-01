import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from './stores/portfolioStore';
import { Layout } from './components/Layout/Layout';
import { TabId } from './components/Layout/Header';

// Components
import { PortfolioSummary } from './components/Portfolio/PortfolioSummary';
import { StrategyPayoff } from './components/Charts/StrategyPayoff';
import { GreeksOverview } from './components/Charts/GreeksOverview';
import { OptionsBoard } from './components/OptionsBoard/OptionsBoard';
import PortfolioTableV2 from './components/Portfolio/PortfolioTableV2';
import { IVRankChart } from './components/Charts/IVRankChart';
import { LoadingSpinner } from './components/Common/LoadingSpinner';
import { ErrorMessage } from './components/Common/ErrorMessage';
import { AMMDashboard } from './components/AMM/AMMDashboard';
import apiClient from './services/api';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  const {
    optionsBoard: options,
    positions,
    isLoading: loading,
    error,
    selectedExpiry,
    fetchOptionsBoard,
    fetchPortfolio,
    fetchTradeLog,
    connectWebSocket,
    disconnectWebSocket,
    isConnected, // Added this field to store if possible, otherwise will check connection status
  } = usePortfolioStore();

  // Initialize data on mount
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
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
    return () => { disconnectWebSocket(); };
  }, [connectWebSocket, disconnectWebSocket]);


  const handleExportJson = async () => {
    try { await apiClient.exportData(); } catch (err) { console.error('Export failed:', err); }
  };

  const handleExportMd = async () => {
    // Placeholder, assume same endpoint or different logic
    try { await apiClient.exportData(); } catch (err) { console.error('Export failed:', err); }
  };

  if (loading && options.length === 0 && positions.length === 0) {
    return (
      <div className="min-h-screen bg-[#0B0E14] flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading Risk Engine..." />
      </div>
    );
  }

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      isConnected={true} // TODO: Expose isConnected from store or hook
      onReconnect={() => connectWebSocket()}
      onExportJson={handleExportJson}
      onExportMd={handleExportMd}
    >
      {error && <ErrorMessage message={error} />}

      {/* DASHBOARD TAB */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6 animate-fadeIn">
          <PortfolioSummary />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Col: Payoff & Greeks */}
            <div className="lg:col-span-2 space-y-6">
              <StrategyPayoff />
              <GreeksOverview />
            </div>

            {/* Right Col: Positions List */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 flex flex-col h-full">
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-semibold">Active Positions</h3>
              </div>
              <div className="flex-1 overflow-auto">
                {/* Simplified wrapper to fit sidebar style */}
                <div className="p-2">
                  <PortfolioTableV2 />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ANALYTICS TAB */}
      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 animate-fadeIn">
          <div className="xl:col-span-2 bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h2 className="text-xl font-semibold mb-4">IV Rank & Volatility</h2>
            <IVRankChart baseCoin="BTC" symbol="BTCUSDT" days={365} height="500px" />
          </div>

          <div className="space-y-4">
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
              <h3 className="font-semibold mb-2">Delta Analytics (Coming Soon)</h3>
              <p className="text-sm text-gray-400">Whale trades and volume delta analysis modules will appear here.</p>
            </div>
          </div>
        </div>
      )}

      {/* CONSTRUCTOR TAB */}
      {activeTab === 'constructor' && (
        <div className="flex items-center justify-center h-[60vh] text-gray-500 animate-fadeIn">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-400 mb-2">Strategy Builder</h2>
            <p>Construction module coming in Phase 3.</p>
          </div>
        </div>
      )}

      {/* TRADING TAB */}
      {activeTab === 'trading' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <OptionsBoard />
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="font-semibold mb-3">Orders & Executions</h3>
            <PortfolioTableV2 />
          </div>
        </div>
      )}

      {/* AMM TAB */}
      {activeTab === 'amm' && (
        <div className="animate-fadeIn">
          <AMMDashboard />
        </div>
      )}

    </Layout>
  );
};

export default App;

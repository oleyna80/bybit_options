import React from 'react';
import { BarChart3, Settings, Download, LayoutDashboard, LineChart, Hammer, TrendingUp, PieChart } from 'lucide-react';

export type TabId = 'dashboard' | 'analytics' | 'constructor' | 'trading' | 'amm';

interface HeaderProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  onExportJson?: () => void;
  onExportMd?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  onExportJson,
  onExportMd
}) => {
  const tabs: { id: TabId; label: string; desc: string; icon: React.ReactNode }[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      desc: 'Portfolio & Risk',
      icon: <LayoutDashboard className="w-4 h-4" />
    },
    {
      id: 'analytics',
      label: 'Analytics',
      desc: 'Delta & Greeks',
      icon: <LineChart className="w-4 h-4" />
    },
    {
      id: 'constructor',
      label: 'Constructor',
      desc: 'Strategy Builder',
      icon: <Hammer className="w-4 h-4" />
    },
    {
      id: 'trading',
      label: 'Trading',
      desc: 'Options Board',
      icon: <TrendingUp className="w-4 h-4" />
    },
    {
      id: 'amm',
      label: 'AMM',
      desc: 'Market Maker',
      icon: <PieChart className="w-4 h-4" />
    },
  ];

  return (
    <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50 backdrop-blur-md bg-opacity-90">
      <div className="max-w-[1920px] mx-auto">
        <div className="flex items-center justify-between px-6 py-4">
          {/* Logo Section */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3 group">
              <div className="p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors">
                <BarChart3 className="h-6 w-6 text-blue-400 group-hover:text-blue-300" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                  Bybit Risk Engine
                </h1>
                <div className="text-xs text-blue-400/80 font-medium tracking-wider">
                  DELTA VOLUME ANALYTICS
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex items-center space-x-1 ml-6">
              {tabs.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => onTabChange(tab.id)}
                    className={`
                      relative group flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all duration-200
                      ${isActive
                        ? 'bg-blue-500/10 text-white shadow-[0_0_20px_rgba(59,130,246,0.15)] ring-1 ring-blue-500/30'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                      }
                    `}
                  >
                    <div className={`${isActive ? 'text-blue-400' : 'text-gray-500 group-hover:text-gray-400'}`}>
                      {tab.icon}
                    </div>
                    <div className="text-left">
                      <div className={`text-sm font-semibold leading-none ${isActive ? 'text-blue-100' : ''}`}>
                        {tab.label}
                      </div>
                      <div className={`text-[10px] mt-1 leading-none ${isActive ? 'text-blue-400/80' : 'text-gray-600'}`}>
                        {tab.desc}
                      </div>
                    </div>

                    {isActive && (
                      <div className="absolute -bottom-[17px] left-0 w-full h-[2px] bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)] rounded-t-full" />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Right Actions */}
          <div className="flex items-center space-x-4">
            <div className="hidden lg:flex items-center px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse mr-2" />
              <span className="text-xs font-medium text-green-400">System Core Active</span>
            </div>

            <div className="h-6 w-px bg-gray-800" />

            <div className="flex items-center space-x-2">
              <button
                onClick={onExportJson}
                className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-md text-xs font-medium transition-all"
                title="Export JSON"
              >
                <Download className="h-3.5 w-3.5" />
                <span>JSON</span>
              </button>
              <button
                className="p-2 hover:bg-gray-800 text-gray-400 hover:text-white rounded-lg transition-colors"
                title="Settings"
              >
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

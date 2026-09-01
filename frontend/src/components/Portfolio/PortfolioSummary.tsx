import React from 'react';
import { Wallet, TrendingUp, AlertTriangle } from 'lucide-react';

export const PortfolioSummary: React.FC = () => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {/* Total Balance Card */}
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Wallet className="w-16 h-16 text-blue-500" />
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Total Balance</h3>
                <div className="text-2xl font-bold text-white mb-2">$125,430.50</div>
                <div className="flex items-center text-xs space-x-2">
                    <span className="text-green-400 flex items-center bg-green-500/10 px-1.5 py-0.5 rounded">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        +2.4%
                    </span>
                    <span className="text-gray-500">vs yesterday</span>
                </div>
            </div>

            {/* Net Delta Card */}
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <TrendingUp className="w-16 h-16 text-purple-500" />
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Net Delta (BTC)</h3>
                <div className="text-2xl font-bold text-red-400 mb-2">-15.20</div>
                <div className="flex items-center text-xs space-x-2">
                    <span className="text-red-400/80 bg-red-500/10 px-1.5 py-0.5 rounded font-medium">Short Exposure</span>
                </div>
            </div>

            {/* Daily Theta Card */}
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <TrendingUp className="w-16 h-16 text-green-500" />
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Daily Theta</h3>
                <div className="text-2xl font-bold text-green-400 mb-2">+$85.00</div>
                <div className="flex items-center text-xs space-x-2">
                    <span className="text-green-400/80 bg-green-500/10 px-1.5 py-0.5 rounded font-medium">Decay Income</span>
                </div>
            </div>

            {/* Margin Status Card */}
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <AlertTriangle className="w-16 h-16 text-yellow-500" />
                </div>
                <div className="flex justify-between items-center mb-1">
                    <h3 className="text-gray-400 text-sm font-medium">Margin Used</h3>
                    <span className="text-xs font-mono text-yellow-500">36%</span>
                </div>
                <div className="text-2xl font-bold text-white mb-3">$45,120</div>

                {/* Progress Bar */}
                <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-green-500 to-yellow-500 w-[36%]" />
                </div>
                <div className="mt-2 text-xs text-gray-500 text-right">Available: $80,310</div>
            </div>
        </div>
    );
};

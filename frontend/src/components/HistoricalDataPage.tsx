import React, { useState } from 'react';
import PriceChart from './Charts/PriceChart';
import { IVRankChart } from './Charts/IVRankChart';
import { BarChart3, TrendingUp, Home } from 'lucide-react';

interface HistoricalDataPageProps {
  onBack?: () => void;
}

const HistoricalDataPage: React.FC<HistoricalDataPageProps> = ({ onBack }) => {
  const [priceDays, setPriceDays] = useState<number>(1825);
  const [ivDays, setIvDays] = useState<number>(30);
  const [showVolume, setShowVolume] = useState<boolean>(true);
  const [symbol, setSymbol] = useState<string>('BTC-PERPETUAL');
  const [baseCoin] = useState<string>('BTC');

  const priceDaysOptions = [
    { label: '1 Year', value: 365 },
    { label: '2 Years', value: 730 },
    { label: '5 Years', value: 1825 },
    { label: 'Max', value: 3650 },
  ];

  const ivDaysOptions = [
    { label: '7 Days', value: 7 },
    { label: '30 Days', value: 30 },
    { label: '90 Days', value: 90 },
    { label: '180 Days', value: 180 },
  ];

  const symbolOptions = [
    { label: 'BTC-PERPETUAL', value: 'BTC-PERPETUAL' },
    { label: 'ETH-PERPETUAL', value: 'ETH-PERPETUAL' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            {onBack && (
              <button
                onClick={onBack}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors px-4 py-2 bg-gray-800 rounded-lg"
              >
                <Home className="h-5 w-5" />
                <span>Back to Dashboard</span>
              </button>
            )}
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-8 w-8 text-blue-400" />
              <h1 className="text-2xl font-bold">Historical Data & IV Rank</h1>
            </div>
          </div>
          <div className="text-sm text-gray-400">
            Real-time and historical market analysis
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-gray-300">
            This page displays historical price data and Implied Volatility (IV) Rank for crypto options.
            IV Rank measures where current implied volatility stands relative to its historical range (0-100%).
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Symbol
          </label>
          <div className="flex flex-wrap gap-2">
            {symbolOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSymbol(option.value)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  symbol === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Price History Period
          </label>
          <div className="flex flex-wrap gap-2">
            {priceDaysOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setPriceDays(option.value)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  priceDays === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            IV Rank Period
          </label>
          <div className="flex flex-wrap gap-2">
            {ivDaysOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setIvDays(option.value)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  ivDays === option.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Chart Options
          </label>
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="showVolume"
                checked={showVolume}
                onChange={(e) => setShowVolume(e.target.checked)}
                className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500 focus:ring-offset-gray-800"
              />
              <label htmlFor="showVolume" className="ml-2 text-sm text-gray-300">
                Show Volume Chart
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRefresh"
                defaultChecked
                className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500 focus:ring-offset-gray-800"
              />
              <label htmlFor="autoRefresh" className="ml-2 text-sm text-gray-300">
                Auto-refresh every 5 minutes
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Price Chart - 2/3 width */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                <h2 className="text-xl font-semibold">{symbol} Price Chart</h2>
              </div>
              <div className="text-sm text-gray-400">
                {priceDays} days • Daily candles • {showVolume ? 'With volume' : 'No volume'}
              </div>
            </div>
            <div className="h-[500px]">
              <PriceChart
                symbol={symbol}
                days={priceDays}
                height={450}
                showVolume={showVolume}
              />
            </div>
          </div>
        </div>

        {/* IV Rank Chart - 1/3 width */}
        <div className="lg:col-span-1">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-purple-400" />
                <h2 className="text-xl font-semibold">{baseCoin} IV Rank</h2>
              </div>
              <div className="text-sm text-gray-400">
                {ivDays} days • 0-100% scale
              </div>
            </div>
            <div className="h-[500px]">
              <IVRankChart
                baseCoin={baseCoin}
                days={ivDays}
                height="450px"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Information Panels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="text-lg font-semibold mb-3 text-blue-400">About Price Chart</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li>• Shows daily OHLCV (Open, High, Low, Close, Volume) data</li>
            <li>• Data sourced from Bybit perpetual futures market</li>
            <li>• Blue area represents closing price over time</li>
            <li>• Volume chart shows trading activity (optional)</li>
            <li>• Tooltip displays detailed candle information</li>
          </ul>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="text-lg font-semibold mb-3 text-purple-400">About IV Rank</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li>• IV Rank = (Current IV - 30d Low) / (30d High - 30d Low) × 100%</li>
            <li>• <span className="text-green-400">Low (0-30%)</span>: Options may be cheap</li>
            <li>• <span className="text-yellow-400">Medium (30-70%)</span>: Fair pricing</li>
            <li>• <span className="text-red-400">High (70-100%)</span>: Options may be expensive</li>
            <li>• Useful for volatility trading strategies</li>
          </ul>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="text-lg font-semibold mb-3 text-green-400">Trading Insights</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li>• Low IV Rank + bullish price trend = Consider buying calls</li>
            <li>• High IV Rank + bearish price trend = Consider selling puts</li>
            <li>• Monitor IV Rank for mean reversion opportunities</li>
            <li>• Combine with technical analysis for better timing</li>
            <li>• Always consider portfolio risk management</li>
          </ul>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-gray-700">
        <div className="text-center text-sm text-gray-400">
          <p>
            Data updates in real-time • Historical data cached for performance • 
            Last updated: {new Date().toLocaleString()}
          </p>
          <p className="mt-2">
            <span className="text-blue-400">Note:</span> IV Rank calculations use 30-day rolling window.
            Price data may have gaps during weekends/holidays.
          </p>
        </div>
      </div>
    </div>
  );
};

export default HistoricalDataPage;
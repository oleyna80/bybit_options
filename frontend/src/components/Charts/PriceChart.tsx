import { useState, useEffect } from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts';
import apiClient from '@/services/api';
import { PriceHistoryResponse } from '@/types';
import { format } from 'date-fns';

interface PriceChartProps {
  symbol?: string;
  days?: number;
  height?: number;
  showVolume?: boolean;
}

const PriceChart = ({
  symbol = 'BTC-PERPETUAL',
  days = 1825,
  height = 400,
  showVolume = false,
}: PriceChartProps) => {
  const [data, setData] = useState<PriceHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [symbol, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getPriceHistory(symbol, days);
      if (response.success) {
        setData(response.data);
      } else {
        setError('Failed to load price history');
      }
    } catch (err: any) {
      setError(err.message || 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'MMM dd, yyyy');
    } catch {
      return timestamp;
    }
  };

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatVolume = (value: number) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
    return value.toFixed(2);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const candle = payload[0].payload;
      return (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-gray-300 font-medium">{formatDate(candle.timestamp)}</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm">
              <span className="text-gray-400">Open: </span>
              <span className="text-white">{formatPrice(candle.open)}</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-400">High: </span>
              <span className="text-white">{formatPrice(candle.high)}</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-400">Low: </span>
              <span className="text-white">{formatPrice(candle.low)}</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-400">Close: </span>
              <span className="text-white">{formatPrice(candle.close)}</span>
            </p>
            {showVolume && (
              <p className="text-sm">
                <span className="text-gray-400">Volume: </span>
                <span className="text-blue-300">{formatVolume(candle.volume)}</span>
              </p>
            )}
            <p className="text-sm">
              <span className="text-gray-400">Change: </span>
              <span className={candle.close >= candle.open ? 'text-green-400' : 'text-red-400'}>
                {((candle.close - candle.open) / candle.open * 100).toFixed(2)}%
              </span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900/50 rounded-lg">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2"></div>
          <p className="text-gray-400">Loading price data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-red-900/20 rounded-lg border border-red-800">
        <div className="text-center p-4">
          <p className="text-red-400 font-medium mb-2">Error loading price chart</p>
          <p className="text-gray-400 text-sm mb-3">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || !data.candles || data.candles.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900/50 rounded-lg">
        <div className="text-center">
          <p className="text-gray-400">No price data available</p>
          <button
            onClick={loadData}
            className="mt-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  const candles = data.candles;
  const latestPrice = candles[candles.length - 1]?.close || 0;
  const minPrice = Math.min(...candles.map(c => c.low));
  const maxPrice = Math.max(...candles.map(c => c.high));

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{symbol} Price Chart</h3>
          <p className="text-sm text-gray-400">
            {days} days • {candles.length} candles • Last: {formatPrice(latestPrice)}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`text-lg font-bold ${latestPrice >= candles[0]?.close ? 'text-green-400' : 'text-red-400'}`}>
            {formatPrice(latestPrice)}
          </span>
          <button
            onClick={loadData}
            className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
            title="Refresh data"
          >
            ↻
          </button>
        </div>
      </div>

      <div className="flex-grow" style={{ height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={candles}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatDate}
              stroke="#6B7280"
              fontSize={12}
              tickMargin={10}
            />
            <YAxis
              stroke="#6B7280"
              fontSize={12}
              tickFormatter={(value) => formatPrice(value).replace('$', '')}
              domain={[minPrice * 0.95, maxPrice * 1.05]}
              tickMargin={10}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={latestPrice}
              stroke="#9CA3AF"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#colorPrice)"
              fillOpacity={0.2}
            />
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {showVolume && (
        <div className="mt-4" style={{ height: '80px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={candles}
              margin={{ top: 0, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatDate}
                stroke="#6B7280"
                fontSize={10}
                tickMargin={5}
              />
              <YAxis
                stroke="#6B7280"
                fontSize={10}
                tickFormatter={formatVolume}
                tickMargin={5}
              />
              <Area
                type="monotone"
                dataKey="volume"
                stroke="#10B981"
                strokeWidth={1}
                fill="url(#colorVolume)"
                fillOpacity={0.6}
              />
              <defs>
                <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-4 flex justify-between text-xs text-gray-500">
        <span>Min: {formatPrice(minPrice)}</span>
        <span>Max: {formatPrice(maxPrice)}</span>
        <span>Range: {formatPrice(maxPrice - minPrice)}</span>
      </div>
    </div>
  );
};

export default PriceChart;
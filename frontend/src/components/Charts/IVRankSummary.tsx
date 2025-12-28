import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';
import apiClient from '@/services/api';
import { IVRankHistoryResponse } from '@/types';
import { format } from 'date-fns';

interface IVRankPanelProps {
  baseCoin?: string;
  days?: number;
  height?: number;
  showCurrentValue?: boolean;
}

const IVRankPanel = ({
  baseCoin = 'BTC',
  days = 30,
  height = 200,
  showCurrentValue = true,
}: IVRankPanelProps) => {
  const [data, setData] = useState<IVRankHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [baseCoin, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getIVRank(baseCoin, days);
      if (response.success) {
        setData(response.data);
      } else {
        setError('Failed to load IV Rank data');
      }
    } catch (err: any) {
      setError(err.message || 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'MMM dd');
    } catch {
      return timestamp;
    }
  };

  const formatIVRank = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getIVRankColor = (value: number) => {
    if (value < 30) return '#10B981'; // green
    if (value < 70) return '#F59E0B'; // yellow
    return '#EF4444'; // red
  };

  const getIVRankStatus = (value: number) => {
    if (value < 30) return 'Low';
    if (value < 70) return 'Medium';
    return 'High';
  };

  const getIVRankDescription = (value: number) => {
    if (value < 30) return 'Implied volatility is relatively low';
    if (value < 70) return 'Implied volatility is at moderate levels';
    return 'Implied volatility is relatively high';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload;
      const color = getIVRankColor(point.iv_rank);
      return (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-gray-300 font-medium">{formatDate(point.timestamp)}</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm">
              <span className="text-gray-400">IV Rank: </span>
              <span className="font-bold" style={{ color }}>
                {formatIVRank(point.iv_rank)}
              </span>
            </p>
            <p className="text-sm">
              <span className="text-gray-400">Current IV: </span>
              <span className="text-white">{(point.current_iv * 100).toFixed(1)}%</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-400">30d Range: </span>
              <span className="text-white">
                {(point.min_iv_30d * 100).toFixed(1)}% - {(point.max_iv_30d * 100).toFixed(1)}%
              </span>
            </p>
            <p className="text-sm">
              <span className="text-gray-400">Status: </span>
              <span className="font-medium" style={{ color }}>
                {getIVRankStatus(point.iv_rank)}
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
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500 mb-2"></div>
          <p className="text-gray-400">Loading IV Rank data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-red-900/20 rounded-lg border border-red-800">
        <div className="text-center p-4">
          <p className="text-red-400 font-medium mb-2">Error loading IV Rank</p>
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

  if (!data || !data.iv_rank_data || data.iv_rank_data.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900/50 rounded-lg">
        <div className="text-center">
          <p className="text-gray-400">No IV Rank data available</p>
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

  const ivRankData = data.iv_rank_data;
  const latestPoint = ivRankData[ivRankData.length - 1];
  const currentIVRank = latestPoint?.iv_rank || 0;
  const currentIV = latestPoint?.current_iv || 0;

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{baseCoin} IV Rank</h3>
          <p className="text-sm text-gray-400">
            Historical IV Rank (0-100%) • {days} days • {ivRankData.length} points
          </p>
        </div>
        
        {showCurrentValue && latestPoint && (
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="flex items-center">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: getIVRankColor(currentIVRank) }}
                ></div>
                <span className="text-2xl font-bold" style={{ color: getIVRankColor(currentIVRank) }}>
                  {formatIVRank(currentIVRank)}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">{getIVRankStatus(currentIVRank)} • {getIVRankDescription(currentIVRank)}</p>
            </div>
            <button
              onClick={loadData}
              className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
              title="Refresh data"
            >
              ↻
            </button>
          </div>
        )}
      </div>

      <div className="flex-grow" style={{ height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={ivRankData}
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
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
              tickMargin={10}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Reference areas for IV Rank zones */}
            <ReferenceArea y1={0} y2={30} fill="#10B981" fillOpacity={0.1} />
            <ReferenceArea y1={30} y2={70} fill="#F59E0B" fillOpacity={0.1} />
            <ReferenceArea y1={70} y2={100} fill="#EF4444" fillOpacity={0.1} />
            
            {/* Reference lines */}
            <ReferenceLine y={30} stroke="#10B981" strokeDasharray="3 3" strokeWidth={1} />
            <ReferenceLine y={70} stroke="#EF4444" strokeDasharray="3 3" strokeWidth={1} />
            <ReferenceLine y={50} stroke="#6B7280" strokeDasharray="3 3" strokeWidth={0.5} />
            
            {/* IV Rank line */}
            <Line
              type="monotone"
              dataKey="iv_rank"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: '#8B5CF6' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Current IV</span>
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
          </div>
          <p className="text-xl font-bold text-white mt-1">
            {(currentIV * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-400 mt-1">Annualized implied volatility</p>
        </div>
        
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">30d Range</span>
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
          </div>
          <p className="text-xl font-bold text-white mt-1">
            {(latestPoint?.min_iv_30d * 100).toFixed(1)}% - {(latestPoint?.max_iv_30d * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-400 mt-1">IV range over last 30 days</p>
        </div>
        
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Status</span>
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: getIVRankColor(currentIVRank) }}
            ></div>
          </div>
          <p
            className="text-xl font-bold mt-1"
            style={{ color: getIVRankColor(currentIVRank) }}
          >
            {getIVRankStatus(currentIVRank)}
          </p>
          <p className="text-xs text-gray-400 mt-1">{getIVRankDescription(currentIVRank)}</p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-1"></div>
            <span>Low (0-30%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-yellow-500 mr-1"></div>
            <span>Medium (30-70%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-red-500 mr-1"></div>
            <span>High (70-100%)</span>
          </div>
        </div>
        <div className="text-right">
          <span className="text-purple-400">IV Rank measures where current IV stands relative to its 30-day range</span>
        </div>
      </div>
    </div>
  );
};

export default IVRankPanel;
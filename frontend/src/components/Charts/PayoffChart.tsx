import React, { useState } from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from 'recharts';
import { PayoffChartData } from '../../types';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import { TrendingUp, TrendingDown, Target, Zap } from 'lucide-react';

// Mock data for development
const mockChartData: PayoffChartData = {
  current_price: 95000.50,
  price_range: [76000, 78000, 80000, 82000, 84000, 86000, 88000, 90000, 92000, 94000, 96000, 98000, 100000, 102000, 104000, 106000, 108000, 110000, 112000, 114000],
  pnl: [-1500, -1200, -900, -600, -300, 0, 300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000, 2700, 2400, 2100, 1800],
  breakeven_points: [89000, 101000],
  max_profit: 4500.50,
  max_loss: -1800.75,
};

interface PayoffChartProps {
  data?: PayoffChartData;
  isLoading?: boolean;
  error?: string | null;
  showWithTheta?: boolean;
  onToggleTheta?: (show: boolean) => void;
}

export const PayoffChart: React.FC<PayoffChartProps> = ({
  data = mockChartData,
  isLoading = false,
  error = null,
  showWithTheta = false,
  onToggleTheta,
}) => {
  const [showBreakeven, setShowBreakeven] = useState(true);
  const [selectedExpiry, setSelectedExpiry] = useState('19DEC25');

  // Prepare chart data
  const chartData = data.price_range.map((price, index) => ({
    price,
    pnl: data.pnl[index],
    pnlWithTheta: data.pnl[index] - 500, // Mock theta adjustment
  }));

  // Find current price index
  const currentPriceIndex = data.price_range.findIndex(
    price => Math.abs(price - data.current_price) < 1000
  );
  const currentPnl = currentPriceIndex >= 0 ? data.pnl[currentPriceIndex] : 0;

  const expiryOptions = ['19DEC25', '26DEC25', '2JAN26'];

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Payoff Chart</h2>
        </div>
        <div className="card-content">
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" text="Loading chart data..." />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="card-title">Payoff at Expiry</h2>
            <p className="text-sm text-muted-foreground">
              Current P&L: 
              <span className={`font-semibold ml-1 ${currentPnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                ${currentPnl.toFixed(2)}
              </span>
              {' • '}
              Underlying: <span className="font-semibold">${data.current_price.toLocaleString()}</span>
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm">Expiry:</label>
              <select
                value={selectedExpiry}
                onChange={(e) => setSelectedExpiry(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-1 text-sm"
              >
                {expiryOptions.map(expiry => (
                  <option key={expiry} value={expiry}>{expiry}</option>
                ))}
              </select>
            </div>
            
            <button
              onClick={() => onToggleTheta?.(!showWithTheta)}
              className={`btn btn-outline btn-sm flex items-center gap-2 ${showWithTheta ? 'bg-primary/10' : ''}`}
            >
              <Zap className="h-4 w-4" />
              {showWithTheta ? 'With Theta' : 'Without Theta'}
            </button>
          </div>
        </div>
      </div>
      
      <div className="card-content">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="price"
                label={{ value: 'Underlying Price ($)', position: 'insideBottom', offset: -5 }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <YAxis
                label={{ value: 'P&L ($)', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => `$${value}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'P&L']}
                labelFormatter={(label) => `Price: $${label.toLocaleString()}`}
              />
              <Legend />
              
              {/* Zero line */}
              <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="3 3" />
              
              {/* Current price line */}
              <ReferenceLine
                x={data.current_price}
                stroke="#3B82F6"
                label={{
                  value: 'Current',
                  position: 'top',
                  fill: '#3B82F6',
                  fontSize: 12,
                }}
              />
              
              {/* Breakeven points */}
              {showBreakeven && data.breakeven_points.map((point, index) => (
                <ReferenceLine
                  key={index}
                  x={point}
                  stroke="#10B981"
                  strokeDasharray="3 3"
                  label={{
                    value: `BE${index + 1}`,
                    position: 'top',
                    fill: '#10B981',
                    fontSize: 12,
                  }}
                />
              ))}
              
              {/* Payoff area */}
              <Area
                type="monotone"
                dataKey={showWithTheta ? 'pnlWithTheta' : 'pnl'}
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.2}
                name="Portfolio P&L"
              />
              
              {/* Max profit line */}
              <ReferenceLine
                y={data.max_profit}
                stroke="#10B981"
                strokeDasharray="3 3"
                label={{
                  value: `Max: $${data.max_profit.toFixed(0)}`,
                  position: 'right',
                  fill: '#10B981',
                  fontSize: 12,
                }}
              />
              
              {/* Max loss line */}
              <ReferenceLine
                y={data.max_loss}
                stroke="#EF4444"
                strokeDasharray="3 3"
                label={{
                  value: `Max Loss: $${Math.abs(data.max_loss).toFixed(0)}`,
                  position: 'right',
                  fill: '#EF4444',
                  fontSize: 12,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="space-y-2 p-4 rounded-lg bg-success/5 border border-success/20">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-success-600" />
              <div className="text-sm font-medium text-success-600">Max Profit</div>
            </div>
            <div className="text-2xl font-bold">${data.max_profit.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">
              At ${data.price_range[data.pnl.indexOf(data.max_profit)]?.toLocaleString() || 'N/A'}
            </div>
          </div>
          
          <div className="space-y-2 p-4 rounded-lg bg-danger/5 border border-danger/20">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-danger-600" />
              <div className="text-sm font-medium text-danger-600">Max Loss</div>
            </div>
            <div className="text-2xl font-bold">${Math.abs(data.max_loss).toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">
              Worst case scenario
            </div>
          </div>
          
          <div className="space-y-2 p-4 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-primary-600" />
              <div className="text-sm font-medium text-primary-600">Breakeven Points</div>
            </div>
            <div className="text-2xl font-bold">
              {data.breakeven_points.length}
            </div>
            <div className="text-xs text-muted-foreground">
              {data.breakeven_points.map(p => `$${p.toLocaleString()}`).join(', ')}
            </div>
          </div>
          
          <div className="space-y-2 p-4 rounded-lg bg-warning/5 border border-warning/20">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-warning-600" />
              <div className="text-sm font-medium text-warning-600">Theta Impact</div>
            </div>
            <div className="text-2xl font-bold">${showWithTheta ? '500' : '0'}/day</div>
            <div className="text-xs text-muted-foreground">
              {showWithTheta ? 'With time decay' : 'No time decay'}
            </div>
          </div>
        </div>
        
        {/* Controls and info */}
        <div className="mt-6 pt-6 border-t">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showBreakeven}
                  onChange={(e) => setShowBreakeven(e.target.checked)}
                  className="rounded border-gray-300"
                />
                Show breakeven points
              </label>
              
              <div className="text-sm text-muted-foreground">
                Days to expiry: <span className="font-semibold">7</span>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-primary"></div>
                <span>Portfolio P&L</span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-3 h-3 rounded-full bg-success"></div>
                <span>Max profit zone</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
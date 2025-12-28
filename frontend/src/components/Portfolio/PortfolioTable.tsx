import React, { useState, useEffect } from 'react';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  ColumnDef,
  SortingState,
} from '@tanstack/react-table';
import { PositionModel, PositionSide, PositionType, OptionType } from '../../types';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import apiClient from '../../services/api';

// Helper function to parse option symbol
function parseOptionSymbol(symbol: string): {
  base_coin: string;
  series: string;
  strike: number;
  option_type: OptionType;
} | null {
  // Format: BTC-9JAN26-92000-C-USDT
  const parts = symbol.split('-');
  if (parts.length !== 5) return null;
  
  const base_coin = parts[0];
  const series = parts[1];
  const strike = parseFloat(parts[2]);
  const option_code = parts[3];
  
  const option_type = option_code === 'C' ? OptionType.CALL : OptionType.PUT;
  
  return { base_coin, series, strike, option_type };
}

// Helper function to convert API position to PositionModel
function convertApiPosition(apiPos: any): PositionModel {
  const isOption = apiPos._category === 'option';
  const parsedSymbol = isOption ? parseOptionSymbol(apiPos.symbol) : null;
  
  // Parse Greeks from API (they are strings)
  const delta = parseFloat(apiPos.delta || '0');
  const gamma = parseFloat(apiPos.gamma || '0');
  const vega = parseFloat(apiPos.vega || '0');
  const theta = parseFloat(apiPos.theta || '0');
  
  // Convert to our Greek format
  // Note: API returns delta in BTC units, gamma in BTC^2, vega/theta in USD
  const greeks = {
    delta_coin: delta,
    gamma_coin: gamma,
    vega_usd: vega,
    theta_usd: theta,
  };
  
  // Calculate mark value: size * markPrice
  const size = parseFloat(apiPos.size || '0');
  const markPrice = parseFloat(apiPos.markPrice || '0');
  const avgPrice = parseFloat(apiPos.avgPrice || '0');
  const unrealisedPnl = parseFloat(apiPos.unrealisedPnl || '0');
  
  const markValue = size * markPrice * (apiPos.side === 'Sell' ? -1 : 1);
  const entryPrice = avgPrice;
  const unrealizedPnl = unrealisedPnl;
  
  return {
    symbol: apiPos.symbol,
    side: apiPos.side === 'Buy' ? PositionSide.BUY : PositionSide.SELL,
    size: Math.abs(size),
    pos_type: isOption ? PositionType.OPTION : PositionType.LINEAR,
    base_coin: parsedSymbol?.base_coin || apiPos.symbol.replace('USDT', ''),
    series: parsedSymbol?.series || null,
    option_type: parsedSymbol?.option_type || null,
    strike: parsedSymbol?.strike || null,
    greeks,
    slippage: null,
    iv_metrics: null,
    gamma_rent: null,
    entry_price: entryPrice || null,
    mark_value: markValue || null,
    unrealized_pnl: unrealizedPnl || null,
  };
}

// Define table columns
const columns: ColumnDef<PositionModel>[] = [
  {
    accessorKey: 'symbol',
    header: 'Symbol',
    cell: ({ row }) => (
      <div className="font-semibold">
        {row.original.symbol}
        {row.original.series && (
          <div className="text-xs text-muted-foreground">
            {row.original.series} • {row.original.strike?.toLocaleString()}
          </div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'side',
    header: 'Side',
    cell: ({ row }) => {
      const isBuy = row.original.side === PositionSide.BUY;
      return (
        <div className={`font-semibold ${isBuy ? 'text-success-600' : 'text-danger-600'}`}>
          {isBuy ? 'BUY' : 'SELL'}
        </div>
      );
    },
  },
  {
    accessorKey: 'size',
    header: 'Size',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.size.toFixed(3)}
      </div>
    ),
  },
  {
    accessorKey: 'entry_price',
    header: 'Entry',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.entry_price?.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }) || '-'}
      </div>
    ),
  },
  {
    accessorKey: 'mark_value',
    header: 'Mark',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.mark_value?.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }) || '-'}
      </div>
    ),
  },
  {
    accessorKey: 'unrealized_pnl',
    header: 'P&L',
    cell: ({ row }) => {
      const pnl = row.original.unrealized_pnl;
      if (pnl === null || pnl === undefined) return '-';
      
      const isPositive = pnl >= 0;
      const Icon = isPositive ? TrendingUp : TrendingDown;
      
      return (
        <div className={`flex items-center font-mono font-semibold ${isPositive ? 'text-success-600' : 'text-danger-600'}`}>
          <Icon className="h-4 w-4 mr-1" />
          ${Math.abs(pnl).toFixed(2)}
          {row.original.entry_price && (
            <span className="text-xs ml-1">
              ({(pnl / (row.original.entry_price * Math.abs(row.original.size)) * 100).toFixed(2)}%)
            </span>
          )}
        </div>
      );
    },
  },
  {
    id: 'greeks',
    header: 'Greeks',
    cell: ({ row }) => (
      <div className="space-y-1">
        <div className="flex items-center text-xs">
          <span className="w-12 text-muted-foreground">Δ:</span>
          <span className={`font-mono ${row.original.greeks.delta_coin >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {row.original.greeks.delta_coin.toFixed(4)}
          </span>
        </div>
        <div className="flex items-center text-xs">
          <span className="w-12 text-muted-foreground">Γ:</span>
          <span className="font-mono">
            {row.original.greeks.gamma_coin.toFixed(6)}
          </span>
        </div>
        <div className="flex items-center text-xs">
          <span className="w-12 text-muted-foreground">Θ:</span>
          <span className={`font-mono ${row.original.greeks.theta_usd >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {row.original.greeks.theta_usd.toFixed(2)}
          </span>
        </div>
      </div>
    ),
  },
  {
    id: 'actions',
    header: '',
    cell: () => (
      <button className="btn btn-outline btn-sm">
        Close
      </button>
    ),
  },
];

interface PortfolioTableProps {
  isLoading?: boolean;
  error?: string | null;
}

export const PortfolioTable: React.FC<PortfolioTableProps> = ({
  isLoading = false,
  error = null,
}) => {
  const [data, setData] = useState<PositionModel[]>([]);
  const [internalLoading, setInternalLoading] = useState<boolean>(true);
  const [internalError, setInternalError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([{ id: 'unrealized_pnl', desc: true }]);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Load positions from API
  useEffect(() => {
    const loadPositions = async () => {
      try {
        setInternalLoading(true);
        setInternalError(null);
        
        const response = await apiClient.getPositions();
        
        if (response.success) {
          // Convert API positions to PositionModel
          const apiPositions = response.data as any[];
          const positions = apiPositions.map(convertApiPosition);
          setData(positions);
          setLastUpdate(new Date().toLocaleTimeString());
        } else {
          setInternalError('Failed to load positions');
        }
      } catch (err: any) {
        setInternalError(err.message || 'Network error');
        console.error('Error loading positions:', err);
      } finally {
        setInternalLoading(false);
      }
    };

    loadPositions();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadPositions, 30000);
    return () => clearInterval(interval);
  }, []);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  // Calculate aggregated metrics
  const totalPnl = data.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
  const totalDelta = data.reduce((sum, pos) => sum + pos.greeks.delta_coin, 0);
  const totalTheta = data.reduce((sum, pos) => sum + pos.greeks.theta_usd, 0);
  const totalVega = data.reduce((sum, pos) => sum + pos.greeks.vega_usd, 0);

  const displayError = error || internalError;
  const displayLoading = isLoading || internalLoading;

  if (displayError) {
    return <ErrorMessage message={displayError} />;
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="card-title">Portfolio Positions</h2>
            <p className="text-sm text-muted-foreground">
              {data.length} positions • Total P&L:
              <span className={`font-semibold ml-1 ${totalPnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                ${totalPnl.toFixed(2)}
              </span>
            </p>
          </div>
        </div>
      </div>
      
      <div className="card-content">
        {/* Aggregated metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Total Delta</div>
            <div className={`text-2xl font-bold ${totalDelta >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
              {totalDelta.toFixed(4)}
              {Math.abs(totalDelta) < 0.01 && (
                <Minus className="inline h-4 w-4 ml-1 text-muted-foreground" />
              )}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {totalDelta >= 0 ? 'Long' : 'Short'} exposure
            </div>
          </div>
          
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Total Theta</div>
            <div className={`text-2xl font-bold ${totalTheta >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
              ${totalTheta.toFixed(2)}/day
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {totalTheta >= 0 ? 'Earning' : 'Paying'} time decay
            </div>
          </div>
          
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Total Vega</div>
            <div className="text-2xl font-bold">
              ${totalVega.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Volatility exposure
            </div>
          </div>
          
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Positions</div>
            <div className="text-2xl font-bold">
              {data.length}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {data.filter(p => p.pos_type === PositionType.OPTION).length} options
            </div>
          </div>
        </div>
        
        {displayLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                {table.getHeaderGroups().map(headerGroup => (
                  <tr key={headerGroup.id} className="border-b">
                    {headerGroup.headers.map(header => (
                      <th
                        key={header.id}
                        className="text-left py-3 px-4 font-semibold text-sm text-muted-foreground"
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        <div className="flex items-center cursor-pointer hover:text-foreground">
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                          {{
                            asc: ' ↑',
                            desc: ' ↓',
                          }[header.column.getIsSorted() as string] ?? null}
                        </div>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map(row => (
                  <tr
                    key={row.id}
                    className="border-b hover:bg-muted/50"
                  >
                    {row.getVisibleCells().map(cell => (
                      <td key={cell.id} className="py-3 px-4">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            
            {data.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                No positions in portfolio
              </div>
            )}
          </div>
        )}
        
        <div className="mt-6 pt-6 border-t">
          <div className="text-sm text-muted-foreground">
            <div className="flex items-center justify-between">
              <div>
                Last updated: {lastUpdate || 'Never'}
              </div>
              <div className="flex items-center gap-4">
                <div className={`chip ${totalDelta >= 0 ? 'chip-default' : 'chip-secondary'}`}>
                  Delta: {totalDelta >= 0 ? 'Long' : 'Short'}
                </div>
                <div className={`chip ${totalTheta >= 0 ? 'chip-default' : 'chip-secondary'}`}>
                  Theta: {totalTheta >= 0 ? 'Positive' : 'Negative'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
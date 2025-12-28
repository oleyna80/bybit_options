import React, { useState } from 'react';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { TradeEntry, PositionSide } from '../../types';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import { TrendingUp, TrendingDown, Calendar, Download } from 'lucide-react';
import { format } from 'date-fns';

// Mock data for development
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
  {
    timestamp: '2025-12-18T09:45:00Z',
    symbol: 'BTC-19DEC25-95000-P-USDT',
    side: PositionSide.SELL,
    size: 0.5,
    price: 800.8,
    fee: 0.40,
    role: 'Maker',
    iv: 0.66,
    pnl: -25.3,
  },
  {
    timestamp: '2025-12-17T14:20:00Z',
    symbol: 'BTCUSDT',
    side: PositionSide.BUY,
    size: 0.2,
    price: 95000,
    fee: 3.80,
    role: 'Taker',
    iv: null,
    pnl: 500,
  },
  {
    timestamp: '2025-12-17T11:15:00Z',
    symbol: 'ETH-19DEC25-3500-C-USDT',
    side: PositionSide.BUY,
    size: 5.0,
    price: 245.6,
    fee: 1.23,
    role: 'Maker',
    iv: 0.72,
    pnl: 123.45,
  },
  {
    timestamp: '2025-12-16T16:45:00Z',
    symbol: 'BTC-26DEC25-105000-C-USDT',
    side: PositionSide.SELL,
    size: 2.0,
    price: 567.8,
    fee: 1.14,
    role: 'Taker',
    iv: 0.68,
    pnl: -45.67,
  },
];

// Define table columns
const columns: ColumnDef<TradeEntry>[] = [
  {
    accessorKey: 'timestamp',
    header: 'Time',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="font-medium">
          {format(new Date(row.original.timestamp), 'HH:mm')}
        </div>
        <div className="text-xs text-muted-foreground">
          {format(new Date(row.original.timestamp), 'MMM dd')}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'symbol',
    header: 'Symbol',
    cell: ({ row }) => (
      <div className="font-semibold">
        {row.original.symbol}
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
    accessorKey: 'price',
    header: 'Price',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.price.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}
      </div>
    ),
  },
  {
    accessorKey: 'fee',
    header: 'Fee',
    cell: ({ row }) => (
      <div className="font-mono text-muted-foreground">
        ${row.original.fee.toFixed(2)}
      </div>
    ),
  },
  {
    accessorKey: 'role',
    header: 'Role',
    cell: ({ row }) => (
      <div className={`chip ${row.original.role === 'Maker' ? 'chip-default' : 'chip-outline'}`}>
        {row.original.role}
      </div>
    ),
  },
  {
    accessorKey: 'iv',
    header: 'IV',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.iv ? `${(row.original.iv * 100).toFixed(1)}%` : '-'}
      </div>
    ),
  },
  {
    accessorKey: 'pnl',
    header: 'P&L',
    cell: ({ row }) => {
      const pnl = row.original.pnl;
      if (pnl === null) return '-';
      
      const isPositive = pnl >= 0;
      const Icon = isPositive ? TrendingUp : TrendingDown;
      
      return (
        <div className={`flex items-center font-mono font-semibold ${isPositive ? 'text-success-600' : 'text-danger-600'}`}>
          <Icon className="h-4 w-4 mr-1" />
          ${Math.abs(pnl).toFixed(2)}
        </div>
      );
    },
  },
];

interface TradeLogProps {
  isLoading?: boolean;
  error?: string | null;
  onExport?: () => void;
}

export const TradeLog: React.FC<TradeLogProps> = ({
  isLoading = false,
  error = null,
  onExport,
}) => {
  const [data] = useState<TradeEntry[]>(mockTrades);
  const [sorting, setSorting] = useState<SortingState>([{ id: 'timestamp', desc: true }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [dateRange, setDateRange] = useState<'1d' | '7d' | '30d' | 'all'>('7d');
  const [selectedSide, setSelectedSide] = useState<string>('ALL');

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  // Calculate summary metrics
  const totalTrades = data.length;
  const totalVolume = data.reduce((sum, trade) => sum + trade.size * trade.price, 0);
  const totalFees = data.reduce((sum, trade) => sum + trade.fee, 0);
  const totalPnl = data.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
  const winRate = data.filter(trade => (trade.pnl || 0) > 0).length / totalTrades * 100;

  const dateRangeOptions = [
    { value: '1d', label: '1 Day' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: 'all', label: 'All Time' },
  ];

  const sideOptions = [
    { value: 'ALL', label: 'All Sides' },
    { value: 'BUY', label: 'Buy Only' },
    { value: 'SELL', label: 'Sell Only' },
  ];

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="card-title">Trade Log</h2>
            <p className="text-sm text-muted-foreground">
              {totalTrades} trades • Total P&L: 
              <span className={`font-semibold ml-1 ${totalPnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                ${totalPnl.toFixed(2)}
              </span>
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={onExport}
              className="btn btn-outline flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 pt-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Date Range</label>
            <div className="flex space-x-1">
              {dateRangeOptions.map(option => (
                <button
                  key={option.value}
                  onClick={() => setDateRange(option.value as any)}
                  className={`chip ${dateRange === option.value ? 'chip-default' : 'chip-outline'}`}
                >
                  <Calendar className="h-3 w-3 mr-1" />
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          
          <div>
            <label className="text-sm font-medium mb-1 block">Side</label>
            <div className="flex space-x-1">
              {sideOptions.map(option => (
                <button
                  key={option.value}
                  onClick={() => setSelectedSide(option.value)}
                  className={`chip ${selectedSide === option.value ? 'chip-default' : 'chip-outline'}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          
          <div className="ml-auto">
            <div className="text-sm text-muted-foreground">
              Last updated: {format(new Date(), 'HH:mm:ss')}
            </div>
          </div>
        </div>
      </div>
      
      <div className="card-content">
        {/* Summary metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Total Volume</div>
            <div className="text-2xl font-bold">
              ${(totalVolume / 1000).toFixed(1)}k
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {totalTrades} trades
            </div>
          </div>
          
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Total Fees</div>
            <div className="text-2xl font-bold">
              ${totalFees.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Average: ${(totalFees / totalTrades).toFixed(2)}
            </div>
          </div>
          
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Win Rate</div>
            <div className={`text-2xl font-bold ${winRate > 50 ? 'text-success-600' : winRate < 40 ? 'text-danger-600' : ''}`}>
              {winRate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {data.filter(t => (t.pnl || 0) > 0).length} winning trades
            </div>
          </div>
          
          <div className="metric-card p-4">
            <div className="text-sm text-muted-foreground">Avg P&L</div>
            <div className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
              ${(totalPnl / totalTrades).toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Per trade
            </div>
          </div>
        </div>
        
        {isLoading ? (
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
                No trades found for the selected filters
              </div>
            )}
          </div>
        )}
        
        <div className="mt-6 pt-6 border-t">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div>
              Showing {data.length} of {data.length} trades
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-success"></div>
                <span>Profitable trade</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-danger"></div>
                <span>Losing trade</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
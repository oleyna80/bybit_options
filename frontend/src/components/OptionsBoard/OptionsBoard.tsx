import React, { useState, useEffect, useCallback } from 'react';
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
import { OptionRow, OptionType, OptionsFilter, WebSocketMessage } from '../../types';
import { ExportButton } from '../Common/ExportButton';
import { ExpiryFilter } from '../Common/ExpiryFilter';
import { CoinSelector } from '../Common/CoinSelector';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import apiClient from '../../services/api';
import wsClient from '../../services/websocket';

// Define table columns
const columns: ColumnDef<OptionRow>[] = [
  {
    accessorKey: 'strike',
    header: 'Strike',
    cell: ({ row }) => (
      <div className="font-mono font-semibold">
        {row.original.strike.toLocaleString()}
      </div>
    ),
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => {
      const isCall = row.original.type_code === 'C';
      return (
        <div className={`font-semibold ${isCall ? 'text-success-600' : 'text-danger-600'}`}>
          {row.original.type.toUpperCase()}
        </div>
      );
    },
  },
  {
    accessorKey: 'bid',
    header: 'Bid',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.prices.bid.toFixed(1)}
      </div>
    ),
  },
  {
    accessorKey: 'ask',
    header: 'Ask',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.prices.ask.toFixed(1)}
      </div>
    ),
  },
  {
    accessorKey: 'mark',
    header: 'Mark',
    cell: ({ row }) => (
      <div className="font-mono font-semibold">
        {row.original.prices.mark.toFixed(1)}
      </div>
    ),
  },
  {
    accessorKey: 'iv',
    header: 'IV',
    cell: ({ row }) => (
      <div className="font-mono">
        {(row.original.iv.mark * 100).toFixed(1)}%
      </div>
    ),
  },
  {
    accessorKey: 'delta',
    header: 'Delta',
    cell: ({ row }) => {
      const delta = row.original.greeks.delta;
      return (
        <div className={`font-mono ${delta >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
          {delta.toFixed(3)}
        </div>
      );
    },
  },
  {
    accessorKey: 'gamma',
    header: 'Gamma',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.greeks.gamma.toFixed(6)}
      </div>
    ),
  },
  {
    accessorKey: 'vega',
    header: 'Vega',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.greeks.vega.toFixed(2)}
      </div>
    ),
  },
  {
    accessorKey: 'theta',
    header: 'Theta',
    cell: ({ row }) => {
      const theta = row.original.greeks.theta;
      return (
        <div className={`font-mono ${theta >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
          {theta.toFixed(2)}
        </div>
      );
    },
  },
  {
    accessorKey: 'open_interest',
    header: 'OI',
    cell: ({ row }) => (
      <div className="font-mono">
        {row.original.liquidity.open_interest.toLocaleString()}
      </div>
    ),
  },
  {
    id: 'position',
    header: 'Position',
    cell: ({ row }) => {
      const { is_in_portfolio, position_size } = row.original;
      if (!is_in_portfolio) return null;
      
      const isLong = position_size && position_size > 0;
      return (
        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${
          isLong ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'
        }`}>
          {isLong ? 'LONG' : 'SHORT'} {Math.abs(position_size || 0)}
        </div>
      );
    },
  },
];

interface OptionsBoardProps {
  underlyingPrice?: number;
  isLoading?: boolean;
  error?: string | null;
  onExport?: (format: 'json' | 'md') => void;
}

export const OptionsBoard: React.FC<OptionsBoardProps> = ({
  underlyingPrice = 95000.50,
  isLoading: externalLoading = false,
  error: externalError = null,
  onExport,
}) => {
  const [data, setData] = useState<OptionRow[]>([]);
  const [sorting, setSorting] = useState<SortingState>([{ id: 'strike', desc: false }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [selectedCoin, setSelectedCoin] = useState<string>('BTC');
  const [selectedExpiry, setSelectedExpiry] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [coins, setCoins] = useState<string[]>(['BTC']);
  const [coinsLoading, setCoinsLoading] = useState<boolean>(true);
  const [expiryOptions, setExpiryOptions] = useState<string[]>(['ALL']);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Load options board data
  const loadOptionsBoard = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const filters: OptionsFilter = {};

      // Always include the selected coin
      filters.base_coin = selectedCoin;

      if (selectedExpiry !== 'ALL') {
        filters.expiry = selectedExpiry;
      }
      if (selectedType !== 'ALL') {
        filters.option_type = selectedType === 'CALL' ? OptionType.CALL : OptionType.PUT;
      }

      const response = await apiClient.getOptionsBoard(filters);
      
      if (response.success) {
        setData(response.data.options || []);
        
        // Extract unique expiry dates
        const expiries = Array.from(
          new Set(response.data.options.map((opt: OptionRow) => opt.expiry))
        ).sort() as string[];
        setExpiryOptions(['ALL', ...expiries]);
        
        setLastUpdate(new Date().toLocaleTimeString());
      } else {
        setError('Failed to load options data');
      }
    } catch (err: any) {
      setError(err.message || 'Network error');
      console.error('Error loading options board:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedCoin, selectedExpiry, selectedType]);

  // Update options data from WebSocket updates
  const updateOptionsData = useCallback((newData: OptionRow[]) => {
    setData(prevData => {
      // Merge updates: replace existing options with same strike/type/expiry
      const updatedData = [...prevData];
      newData.forEach(newOption => {
        const index = updatedData.findIndex(opt =>
          opt.strike === newOption.strike &&
          opt.type_code === newOption.type_code &&
          opt.expiry === newOption.expiry
        );
        if (index >= 0) {
          updatedData[index] = { ...updatedData[index], ...newOption };
        } else {
          updatedData.push(newOption);
        }
      });
      return updatedData;
    });
    setLastUpdate(new Date().toLocaleTimeString());
  }, []);

  // Load supported coins on mount
  useEffect(() => {
    const loadCoins = async () => {
      try {
        setCoinsLoading(true);
        const response = await apiClient.getCoins();
        if (response.success && response.data.length > 0) {
          setCoins(response.data);
          // Set first coin as default if BTC is not in the list
          if (!response.data.includes('BTC') && response.data.length > 0) {
            setSelectedCoin(response.data[0]);
          }
        }
      } catch (err) {
        console.error('Error loading coins:', err);
        // Keep default BTC if loading fails
      } finally {
        setCoinsLoading(false);
      }
    };
    loadCoins();
  }, []);

  // Load data on mount and when filters change
  useEffect(() => {
    loadOptionsBoard();

    // Subscribe to WebSocket updates
    const unsubscribe = wsClient.subscribe((message: WebSocketMessage) => {
      if (message.type === 'options_board_update') {
        const optionsData = message.data as OptionRow[];
        updateOptionsData(optionsData);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [loadOptionsBoard, updateOptionsData]);

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

  const typeOptions = ['ALL', 'CALL', 'PUT'];

  const handleExport = (format: 'json' | 'md') => {
    if (onExport) {
      onExport(format);
    } else {
      console.log(`Exporting options data as ${format}`, data);
      // In a real implementation, this would trigger a download
      alert(`Exporting ${data.length} options as ${format.toUpperCase()}`);
    }
  };

  // Combine external and internal errors/loading states
  const displayError = externalError || error;
  const displayLoading = externalLoading || isLoading;

  if (displayError) {
    return <ErrorMessage message={displayError} />;
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="card-title">Options Board - {selectedCoin}</h2>
            <p className="text-sm text-muted-foreground">
              Underlying Price: <span className="font-semibold">${underlyingPrice.toLocaleString()}</span>
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <ExportButton onExport={handleExport} />
          </div>
        </div>
        
        <div className="flex flex-wrap items-center gap-4 pt-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Coin</label>
            <CoinSelector
              coins={coins}
              selected={selectedCoin}
              onChange={setSelectedCoin}
              isLoading={coinsLoading}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-1 block">Expiry</label>
            <ExpiryFilter
              options={expiryOptions}
              selected={selectedExpiry}
              onChange={setSelectedExpiry}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-1 block">Type</label>
            <div className="flex space-x-1">
              {typeOptions.map(type => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  className={`chip ${selectedType === type ? 'chip-default' : 'chip-outline'}`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="ml-auto">
            <div className="text-sm text-muted-foreground">
              Showing {data.length} options
            </div>
          </div>
        </div>
      </div>
      
      <div className="card-content">
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
                    className={`border-b hover:bg-muted/50 ${
                      row.original.is_in_portfolio ? 'bg-primary/5' : ''
                    }`}
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
            
            {data.length === 0 && !displayLoading && (
              <div className="text-center py-12 text-muted-foreground">
                No options found for the selected filters
              </div>
            )}
          </div>
        )}
        
        <div className="mt-6 pt-6 border-t">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="space-y-1">
              <div className="text-muted-foreground">Total Options</div>
              <div className="font-semibold">{data.length}</div>
            </div>
            <div className="space-y-1">
              <div className="text-muted-foreground">Calls/Puts</div>
              <div className="font-semibold">
                {data.filter(o => o.type_code === 'C').length}/
                {data.filter(o => o.type_code === 'P').length}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-muted-foreground">Avg IV</div>
              <div className="font-semibold">
                {data.length > 0
                  ? ((data.reduce((sum, o) => sum + o.iv.mark, 0) / data.length) * 100).toFixed(1) + '%'
                  : 'N/A'
                }
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-muted-foreground">Last Update</div>
              <div className="font-semibold">{lastUpdate || 'Never'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
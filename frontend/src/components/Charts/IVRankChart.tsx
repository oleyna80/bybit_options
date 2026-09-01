// frontend/src/components/Charts/IVRankChart.tsx

import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, IChartApi, ISeriesApi, LineSeries, UTCTimestamp } from 'lightweight-charts';
import { fetchIVRankData, fetchPriceHistory, transformToCandlestickData, transformToLineData } from '../../services/ivRankApi';
import type { CandlestickData, LineData } from '../../types/ivrank.types';

/**
 * Props for IVRankChart component
 */
interface IVRankChartProps {
  baseCoin?: string;      // Default: "BTC"
  symbol?: string;        // Default: "BTCUSDT"
  days?: number;          // Default: 365
  height?: string;        // Default: "600px"
}

/**
 * Synchronized dual-chart component showing:
 * 1. Price Chart (Candlesticks) - 60% height
 * 2. IV Rank Indicator (Line) - 20% height
 */
export const IVRankChart: React.FC<IVRankChartProps> = ({
  baseCoin = 'BTC',
  symbol = 'BTCUSDT',
  days = 365,
  height = '600px',
}) => {
  // Refs for chart containers
  const priceChartContainerRef = useRef<HTMLDivElement>(null);
  const ivRankChartContainerRef = useRef<HTMLDivElement>(null);

  // Refs for chart instances
  const priceChartRef = useRef<IChartApi | null>(null);
  const ivRankChartRef = useRef<IChartApi | null>(null);

  const initializedRef = useRef<boolean>(false);
  const resizeLogCountRef = useRef<number>(0);

  // Refs for series
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ivRankSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [priceData, setPriceData] = useState<CandlestickData[]>([]);
  const [ivRankData, setIvRankData] = useState<LineData[]>([]);

  useLayoutEffect(() => {
    if (loading || error) {
      return;
    }

    // Prevent double initialization
    if (initializedRef.current) {
      console.log('Already initialized');
      return;
    }

    if (!priceChartContainerRef.current || !ivRankChartContainerRef.current) {
      console.warn('Containers not found', {
        loading,
        error,
        priceRef: priceChartContainerRef.current,
        ivRef: ivRankChartContainerRef.current,
      });
      return;
    }

    const priceRect = priceChartContainerRef.current.getBoundingClientRect();
    const ivRect = ivRankChartContainerRef.current.getBoundingClientRect();

    console.log('📐 Init attempt sizes', {
      loading,
      error,
      priceRect: { width: priceRect.width, height: priceRect.height, top: priceRect.top, left: priceRect.left },
      ivRect: { width: ivRect.width, height: ivRect.height, top: ivRect.top, left: ivRect.left },
    });

    if (priceRect.width === 0 || priceRect.height === 0) {
      console.warn('Zero size, retrying...');
      return;
    }

    console.log('✅ Initializing charts');

    // Define sync callbacks in outer scope so cleanup can unsubscribe them
    let syncPriceToIv: (() => void) | null = null;
    let syncIvToPrice: (() => void) | null = null;

    try {
      const priceChart = createChart(priceChartContainerRef.current, {
        width: priceRect.width,
        height: priceRect.height,
        layout: {
          background: { color: '#111827' },
          textColor: '#e5e7eb',
        },
        grid: {
          vertLines: { color: '#1f2937' },
          horzLines: { color: '#1f2937' },
        },
        timeScale: {
          borderColor: '#cccccc',
          timeVisible: true,
        },
      });
      priceChartRef.current = priceChart;

      const candlestickSeries = priceChart.addSeries(CandlestickSeries, {
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
      candlestickSeriesRef.current = candlestickSeries;

      const ivChart = createChart(ivRankChartContainerRef.current, {
        width: ivRect.width,
        height: ivRect.height,
        layout: {
          background: { color: '#111827' },
          textColor: '#e5e7eb',
        },
        grid: {
          vertLines: { color: '#1f2937' },
          horzLines: { color: '#1f2937' },
        },
        timeScale: {
          borderColor: '#cccccc',
          visible: true,
        },
      });
      ivRankChartRef.current = ivChart;

      const ivRankSeries = ivChart.addSeries(LineSeries, {
        color: '#2962FF',
        lineWidth: 2,
        priceFormat: {
          type: 'custom',
          formatter: (price: number) => `${price.toFixed(1)}%`,
        },
      });
      ivRankSeriesRef.current = ivRankSeries;

      syncPriceToIv = () => {
        const priceChartInstance = priceChartRef.current;
        const ivChartInstance = ivRankChartRef.current;
        if (!ivChartInstance || !priceChartInstance) return;
        const timeRange = priceChartInstance.timeScale().getVisibleRange();
        if (timeRange && timeRange.from != null && timeRange.to != null) {
          try {
            ivChartInstance.timeScale().setVisibleRange(timeRange);
          } catch (err) {
            console.warn('syncPriceToIv failed', { timeRange, err });
          }
        }
      };

      syncIvToPrice = () => {
        const priceChartInstance = priceChartRef.current;
        const ivChartInstance = ivRankChartRef.current;
        if (!ivChartInstance || !priceChartInstance) return;
        const timeRange = ivChartInstance.timeScale().getVisibleRange();
        if (timeRange && timeRange.from != null && timeRange.to != null) {
          try {
            priceChartInstance.timeScale().setVisibleRange(timeRange);
          } catch (err) {
            console.warn('syncIvToPrice failed', { timeRange, err });
          }
        }
      };

      priceChart.timeScale().subscribeVisibleTimeRangeChange(syncPriceToIv);
      ivChart.timeScale().subscribeVisibleTimeRangeChange(syncIvToPrice);

      initializedRef.current = true;
      console.log('✅ Charts created successfully');
    } catch (error) {
      console.error('❌ Chart error:', error);
    }

    return () => {
      console.log('Cleanup');
      if (priceChartRef.current) {
        if (syncPriceToIv) {
          // Unsubscribe before removing charts to avoid callbacks firing on disposed charts
          const priceTimeScale = priceChartRef.current.timeScale();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          if ((priceTimeScale as any).unsubscribeVisibleTimeRangeChange) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (priceTimeScale as any).unsubscribeVisibleTimeRangeChange(syncPriceToIv);
          }
        }
        priceChartRef.current.remove();
        priceChartRef.current = null;
      }
      if (ivRankChartRef.current) {
        if (syncIvToPrice) {
          const ivTimeScale = ivRankChartRef.current.timeScale();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          if ((ivTimeScale as any).unsubscribeVisibleTimeRangeChange) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (ivTimeScale as any).unsubscribeVisibleTimeRangeChange(syncIvToPrice);
          }
        }
        ivRankChartRef.current.remove();
        ivRankChartRef.current = null;
      }
      candlestickSeriesRef.current = null;
      ivRankSeriesRef.current = null;
      initializedRef.current = false;
    };
  }, [loading, error]);

  useEffect(() => {
    if (!priceChartContainerRef.current || !ivRankChartContainerRef.current) {
      return;
    }

    const handleResize = () => {
      if (priceChartRef.current && priceChartContainerRef.current) {
        const rect = priceChartContainerRef.current.getBoundingClientRect();
        priceChartRef.current.applyOptions({
          width: rect.width,
          height: rect.height,
        });
        if (resizeLogCountRef.current < 5) {
          resizeLogCountRef.current += 1;
          console.log('📐 Resize price container', {
            attempt: resizeLogCountRef.current,
            rect: { width: rect.width, height: rect.height, top: rect.top, left: rect.left },
            initialized: initializedRef.current,
          });
        }
      }
      if (ivRankChartRef.current && ivRankChartContainerRef.current) {
        const rect = ivRankChartContainerRef.current.getBoundingClientRect();
        ivRankChartRef.current.applyOptions({
          width: rect.width,
          height: rect.height,
        });
        if (resizeLogCountRef.current < 5) {
          resizeLogCountRef.current += 1;
          console.log('📐 Resize IV container', {
            attempt: resizeLogCountRef.current,
            rect: { width: rect.width, height: rect.height, top: rect.top, left: rect.left },
            initialized: initializedRef.current,
          });
        }
      }
    };

    const observer = new ResizeObserver(() => {
      handleResize();
    });

    observer.observe(priceChartContainerRef.current);
    observer.observe(ivRankChartContainerRef.current);

    return () => observer.disconnect();
  }, []);

  // Effect 3: Load data (independent of charts)
  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      if (!isMounted) return;

      try {
        setLoading(true);
        setError(null);

        console.log('📊 Loading data...');

        // Fetch both datasets in parallel
        const [priceResponse, ivRankResponse] = await Promise.all([
          fetchPriceHistory(symbol, days),
          fetchIVRankData(baseCoin, days),
        ]);

        if (!isMounted) return;

        console.log('✅ Data loaded:', {
          candles: priceResponse.candles.length,
          ivRank: ivRankResponse.iv_rank_data.length
        });

        // Transform to TradingView format
        const transformedPriceData = transformToCandlestickData(priceResponse.candles);
        const transformedIvRankData = transformToLineData(ivRankResponse.iv_rank_data);

        // Update state
        setPriceData(transformedPriceData);
        setIvRankData(transformedIvRankData);

      } catch (err) {
        console.error('❌ Failed to load chart data:', err);
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load data');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadData();

    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [baseCoin, symbol, days]);

  // Effect 4: Apply data to charts when both ready
  useEffect(() => {
    if (!candlestickSeriesRef.current || !ivRankSeriesRef.current) {
      console.log('⏳ Charts not ready yet');
      return;
    }

    if (priceData.length === 0 && ivRankData.length === 0) {
      console.log('⏳ Data not loaded yet');
      return;
    }

    console.log('🎨 Applying data to charts');

    if (priceData.length > 0) {
      candlestickSeriesRef.current.setData(
        priceData.map(d => ({ ...d, time: d.time as UTCTimestamp }))
      );
    }

    if (ivRankData.length > 0) {
      ivRankSeriesRef.current.setData(
        ivRankData.map(d => ({ ...d, time: d.time as UTCTimestamp }))
      );
    }

    setTimeout(() => {
      if (priceChartRef.current && ivRankChartRef.current) {
        try {
          priceChartRef.current.timeScale().fitContent();
          ivRankChartRef.current.timeScale().fitContent();
          console.log('✅ Charts fitted');
        } catch (err) {
          console.warn('fitContent failed:', err);
        }
      }
    }, 100);
  }, [priceData, ivRankData]);

  // Loading state - show spinner while loading
  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chart data...</p>
          <p className="text-xs text-gray-400 mt-2">
            {baseCoin} • {days} days • {symbol}
          </p>
        </div>
      </div>
    );
  }

  // Error state - show error message
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-6" style={{ height }}>
        <div className="text-center text-red-600 max-w-md">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-xl font-semibold mb-2">Error loading chart</p>
          <p className="text-sm mb-4">{error}</p>
          <p className="text-xs text-gray-500">
            Check your connection and try refreshing the page.
          </p>
          <button
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            onClick={() => window.location.reload()}
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  // Check if we have data to display
  const hasData = priceData.length > 0 || ivRankData.length > 0;

  // Get current IV Rank value safely
  const currentIVRank = ivRankData.length > 0 ? ivRankData[ivRankData.length - 1].value : null;

  // Main render
  return (
    <div className="w-full" style={{ height }}>
      {/* Header */}
      <div className="bg-gray-900 text-white px-4 py-2 flex justify-between items-center">
        <h2 className="text-lg font-semibold">{symbol} - IV Rank Analysis</h2>
        <div className="text-sm text-gray-400">
          {baseCoin} • {days} days
        </div>
      </div>

      {/* Price Chart Container (60% height) */}
      <div
        ref={priceChartContainerRef}
        className="w-full bg-gray-900"
        style={{ 
          height: '360px',
          minHeight: '360px',
          width: '100%',
          position: 'relative'
        }}
      />

      {/* IV Rank Chart Container (20% height) */}
      <div
        ref={ivRankChartContainerRef}
        className="w-full bg-gray-900 border-t border-gray-700"
        style={{ 
          height: '120px',
          minHeight: '120px',
          width: '100%',
          position: 'relative'
        }}
      />

      {/* Legend/Info (20% height) */}
      <div className="bg-gray-800 p-4" style={{ height: '20%' }}>
        {!hasData ? (
          <div className="text-center text-gray-400 py-4">
            <p className="text-lg mb-2">No chart data available</p>
            <p className="text-sm text-gray-500">
              Try changing the parameters or check the data source.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400 mb-1">Current IV Rank</p>
              <p className="text-2xl font-bold">
                {currentIVRank !== null ? `${currentIVRank.toFixed(1)}%` : '—'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">Interpretation</p>
              <p className="text-lg">
                {currentIVRank !== null ? (
                  currentIVRank < 25 ? (
                    <span className="text-green-600">🟢 Low IV - Buy Options</span>
                  ) : currentIVRank > 75 ? (
                    <span className="text-red-600">🔴 High IV - Sell Options</span>
                  ) : (
                    <span className="text-gray-300">⚪ Normal IV</span>
                  )
                ) : (
                  <span className="text-gray-500">—</span>
                )}
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">Data Points</p>
              <p className="text-lg">{priceData.length} candles</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

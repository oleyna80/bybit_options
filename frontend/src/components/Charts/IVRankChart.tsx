// frontend/src/components/Charts/IVRankChart.tsx

import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts';
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

  // Refs for series
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ivRankSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [priceData, setPriceData] = useState<CandlestickData[]>([]);
  const [ivRankData, setIvRankData] = useState<LineData[]>([]);

  // Main effect: Initialize charts and load data
  useEffect(() => {
    let isMounted = true;
    let priceChart: IChartApi | null = null;
    let ivChart: IChartApi | null = null;
    let candlestickSeries: ISeriesApi<'Candlestick'> | null = null;
    let ivRankSeries: ISeriesApi<'Line'> | null = null;
    let hasFittedContent = false; // Track if fitContent has been called

    const initializeCharts = () => {
      // Check if containers exist
      if (!priceChartContainerRef.current || !ivRankChartContainerRef.current) {
        console.warn('Chart containers not found');
        return false;
      }

      const priceContainer = priceChartContainerRef.current;
      const ivContainer = ivRankChartContainerRef.current;

      // Check if containers have valid dimensions
      const priceWidth = priceContainer.clientWidth;
      const priceHeight = priceContainer.clientHeight;
      const ivWidth = ivContainer.clientWidth;
      const ivHeight = ivContainer.clientHeight;

      if (priceWidth === 0 || priceHeight === 0 || ivWidth === 0 || ivHeight === 0) {
        console.warn('Chart containers have zero dimensions:', {
          priceWidth,
          priceHeight,
          ivWidth,
          ivHeight
        });
        return false;
      }

      // Ensure minimum dimensions
      const minWidth = 100;
      const minHeight = 50;
      
      if (priceWidth < minWidth || priceHeight < minHeight ||
          ivWidth < minWidth || ivHeight < minHeight) {
        console.warn('Chart containers below minimum dimensions');
        return false;
      }

      try {
        // Create chart instances
        priceChart = createChart(priceContainer, {
          width: priceWidth,
          height: priceHeight,
          layout: {
            background: { color: '#ffffff' },
            textColor: '#333',
          },
          grid: {
            vertLines: { color: '#f0f0f0' },
            horzLines: { color: '#f0f0f0' },
          },
          timeScale: {
            borderColor: '#cccccc',
            timeVisible: true,
            secondsVisible: false,
          },
          rightPriceScale: {
            borderColor: '#cccccc',
          },
        });

        ivChart = createChart(ivContainer, {
          width: ivWidth,
          height: ivHeight,
          layout: {
            background: { color: '#ffffff' },
            textColor: '#333',
          },
          grid: {
            vertLines: { color: '#f0f0f0' },
            horzLines: { color: '#f0f0f0' },
          },
          timeScale: {
            borderColor: '#cccccc',
            timeVisible: true,
            secondsVisible: false,
          },
          rightPriceScale: {
            borderColor: '#cccccc',
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          },
        });

        // Save chart instances to refs
        priceChartRef.current = priceChart;
        ivRankChartRef.current = ivChart;

        // Add series
        candlestickSeries = (priceChart as any).addCandlestickSeries({
          upColor: '#26a69a',
          downColor: '#ef5350',
          borderVisible: false,
          wickUpColor: '#26a69a',
          wickDownColor: '#ef5350',
        });

        ivRankSeries = (ivChart as any).addLineSeries({
          color: '#2962FF',
          lineWidth: 2,
          priceFormat: {
            type: 'custom',
            formatter: (price: number) => `${price.toFixed(1)}%`,
          },
        });

        // Save series to refs
        candlestickSeriesRef.current = candlestickSeries;
        ivRankSeriesRef.current = ivRankSeries;

        // === TIME SCALE SYNCHRONIZATION ===
        const priceTimeScale = priceChart.timeScale();
        const ivTimeScale = ivChart.timeScale();

        // Sync Price → IV Rank
        priceTimeScale.subscribeVisibleLogicalRangeChange((range) => {
          if (range) {
            ivTimeScale.setVisibleLogicalRange(range);
          }
        });

        // Sync IV Rank → Price
        ivTimeScale.subscribeVisibleLogicalRangeChange((range) => {
          if (range) {
            priceTimeScale.setVisibleLogicalRange(range);
          }
        });

        console.log('Charts initialized successfully with dimensions:', {
          priceWidth,
          priceHeight,
          ivWidth,
          ivHeight
        });
        
        return true;
      } catch (err) {
        console.error('Failed to initialize charts:', err);
        return false;
      }
    };

    const loadData = async () => {
      if (!isMounted) return;

      try {
        setLoading(true);
        setError(null);

        // Initialize charts first if not already initialized
        if (!priceChartRef.current || !ivRankChartRef.current) {
          const initialized = initializeCharts();
          if (!initialized) {
            // Retry after a short delay if containers not ready
            setTimeout(() => {
              if (isMounted) loadData();
            }, 200); // Increased delay for better layout calculation
            return;
          }
        }

        // Fetch both datasets in parallel
        const [priceResponse, ivRankResponse] = await Promise.all([
          fetchPriceHistory(symbol, days),
          fetchIVRankData(baseCoin, days),
        ]);

        if (!isMounted) return;

        // Transform to TradingView format
        const transformedPriceData = transformToCandlestickData(priceResponse.candles);
        const transformedIvRankData = transformToLineData(ivRankResponse.iv_rank_data);

        // Update state
        setPriceData(transformedPriceData);
        setIvRankData(transformedIvRankData);

        // Update chart data directly
        if (candlestickSeriesRef.current && transformedPriceData.length > 0) {
          candlestickSeriesRef.current.setData(
            transformedPriceData.map(d => ({ ...d, time: d.time as UTCTimestamp }))
          );
        }

        if (ivRankSeriesRef.current && transformedIvRankData.length > 0) {
          ivRankSeriesRef.current.setData(
            transformedIvRankData.map(d => ({ ...d, time: d.time as UTCTimestamp }))
          );
        }

        // Fit content after data is set (only on first load)
        if (!hasFittedContent && (transformedPriceData.length > 0 || transformedIvRankData.length > 0)) {
          const fitContentWithRetry = (retryCount = 0) => {
            if (!isMounted) return;
            
            const maxRetries = 3;
            const priceChart = priceChartRef.current;
            const ivChart = ivRankChartRef.current;
            
            if (priceChart && ivChart) {
              try {
                priceChart.timeScale().fitContent();
                ivChart.timeScale().fitContent();
                hasFittedContent = true;
                console.log('fitContent called successfully');
              } catch (err) {
                console.warn('fitContent failed, retrying:', err);
                if (retryCount < maxRetries) {
                  setTimeout(() => fitContentWithRetry(retryCount + 1), 100 * (retryCount + 1));
                }
              }
            } else if (retryCount < maxRetries) {
              // Charts not ready yet, retry
              setTimeout(() => fitContentWithRetry(retryCount + 1), 100 * (retryCount + 1));
            }
          };
          
          // Initial attempt after a short delay
          setTimeout(() => fitContentWithRetry(), 100);
        }

      } catch (err) {
        console.error('Failed to load chart data:', err);
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load data');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Resize handler with debouncing
    let resizeTimeout: number | null = null;
    const handleResize = () => {
      if (resizeTimeout !== null) {
        clearTimeout(resizeTimeout);
      }
      
      resizeTimeout = window.setTimeout(() => {
        if (!isMounted) return;
        
        if (priceChartContainerRef.current && ivRankChartContainerRef.current) {
          const priceWidth = priceChartContainerRef.current.clientWidth;
          const priceHeight = priceChartContainerRef.current.clientHeight;
          const ivWidth = ivRankChartContainerRef.current.clientWidth;
          const ivHeight = ivRankChartContainerRef.current.clientHeight;
          
          // Only resize if dimensions are valid
          if (priceWidth > 0 && priceHeight > 0) {
            priceChartRef.current?.applyOptions({
              width: priceWidth,
              height: priceHeight
            });
          }
          
          if (ivWidth > 0 && ivHeight > 0) {
            ivRankChartRef.current?.applyOptions({
              width: ivWidth,
              height: ivHeight
            });
          }
        }
      }, 150); // Debounce resize events
    };

    // Start loading data
    loadData();

    // Add resize listener
    window.addEventListener('resize', handleResize);

    // Cleanup function
    return () => {
      isMounted = false;
      window.removeEventListener('resize', handleResize);
      
      // Clear resize timeout
      if (resizeTimeout !== null) {
        clearTimeout(resizeTimeout);
      }
      
      // Clean up chart instances
      if (priceChartRef.current) {
        priceChartRef.current.remove();
        priceChartRef.current = null;
      }
      if (ivRankChartRef.current) {
        ivRankChartRef.current.remove();
        ivRankChartRef.current = null;
      }
      
      // Clear series refs
      candlestickSeriesRef.current = null;
      ivRankSeriesRef.current = null;
    };
  }, [baseCoin, symbol, days]);

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
  
  // If no data but not loading/error, show empty state
  if (!hasData) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-500">
          <p className="text-lg mb-2">No chart data available</p>
          <p className="text-sm">
            Try changing the parameters or check the data source.
          </p>
        </div>
      </div>
    );
  }

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
        className="w-full bg-white"
        style={{ height: '60%' }}
      />

      {/* IV Rank Chart Container (20% height) */}
      <div 
        ref={ivRankChartContainerRef}
        className="w-full bg-white border-t border-gray-200"
        style={{ height: '20%' }}
      />

      {/* Legend/Info (20% height) */}
      <div className="bg-gray-50 p-4" style={{ height: '20%' }}>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-600 mb-1">Current IV Rank</p>
            <p className="text-2xl font-bold">
              {currentIVRank !== null ? `${currentIVRank.toFixed(1)}%` : '—'}
            </p>
          </div>
          <div>
            <p className="text-gray-600 mb-1">Interpretation</p>
            <p className="text-lg">
              {currentIVRank !== null ? (
                currentIVRank < 25 ? (
                  <span className="text-green-600">🟢 Low IV - Buy Options</span>
                ) : currentIVRank > 75 ? (
                  <span className="text-red-600">🔴 High IV - Sell Options</span>
                ) : (
                  <span className="text-gray-600">⚪ Normal IV</span>
                )
              ) : (
                <span className="text-gray-400">—</span>
              )}
            </p>
          </div>
          <div>
            <p className="text-gray-600 mb-1">Data Points</p>
            <p className="text-lg">{priceData.length} candles</p>
          </div>
        </div>
      </div>
    </div>
  );
};
import React, { useEffect, useState } from 'react';

interface Position {
  symbol: string;
  side: string;
  size: string;
  avgPrice: string;
  markPrice: string;
  unrealisedPnl: string;
  entry_iv: number | null;
  current_iv: string | null;
  delta?: string;
  gamma?: string;
  vega?: string;
  theta?: string;
  _category: string;
}

interface PositionsResponse {
  count: number;
  positions: Position[];
}

const PortfolioTableV2: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'BTC' | 'ETH' | 'FUTURES'>('BTC');

  useEffect(() => {
    fetchPositions();
    const interval = setInterval(fetchPositions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/v1/positions');
      const data: PositionsResponse = await response.json();
      setPositions(data.positions || []);
    } catch (error) {
      console.error('Failed to fetch positions:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupedPositions = {
    BTC: positions.filter(
      (p) => p.symbol.startsWith('BTC') && p._category === 'option'
    ),
    ETH: positions.filter(
      (p) => p.symbol.startsWith('ETH') && p._category === 'option'
    ),
    FUTURES: positions.filter((p) => p._category === 'linear'),
  };

  const currentPositions = groupedPositions[activeTab];

  const aggregateGreeks = currentPositions.reduce(
    (acc, pos) => ({
      delta: acc.delta + parseFloat(pos.delta || '0'),
      gamma: acc.gamma + parseFloat(pos.gamma || '0'),
      vega: acc.vega + parseFloat(pos.vega || '0'),
      theta: acc.theta + parseFloat(pos.theta || '0'),
    }),
    { delta: 0, gamma: 0, vega: 0, theta: 0 }
  );

  const calculateDTE = (symbol: string): number | null => {
    const match = symbol.match(/(\d{1,2})([A-Z]{3})(\d{2})/);
    if (!match) return null;

    const [, day, month, year] = match;
    const monthMap: Record<string, number> = {
      JAN: 0,
      FEB: 1,
      MAR: 2,
      APR: 3,
      MAY: 4,
      JUN: 5,
      JUL: 6,
      AUG: 7,
      SEP: 8,
      OCT: 9,
      NOV: 10,
      DEC: 11,
    };

    const expiry = new Date(2000 + parseInt(year, 10), monthMap[month], parseInt(day, 10));
    const now = new Date();
    const diffMs = expiry.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    return diffDays >= 0 ? diffDays : 0;
  };

  const formatPnlPercent = (pnl: string, entry: string, size: string): string => {
    const pnlNum = parseFloat(pnl);
    const entryNum = parseFloat(entry);
    const sizeNum = parseFloat(size);

    if (entryNum === 0 || sizeNum === 0) return '0.00';

    const entryValue = entryNum * sizeNum;
    const pnlPercent = (pnlNum / entryValue) * 100;

    return pnlPercent.toFixed(2);
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-400">Loading positions...</div>;
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h2 className="card-title">Portfolio Positions</h2>
          <div className="text-sm text-gray-400">
            {currentPositions.length} positions
          </div>
        </div>
      </div>
      <div className="card-content">
        <div className="flex gap-4 mb-4 border-b border-gray-700">
          {(['BTC', 'ETH', 'FUTURES'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'border-b-2 border-blue-500 text-blue-400'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab} ({groupedPositions[tab].length})
            </button>
          ))}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-gray-400 border-b border-gray-700">
              <tr>
                <th className="px-3 py-2 text-left">Symbol</th>
                <th className="px-3 py-2 text-left">Side</th>
                <th className="px-3 py-2 text-right">Qty</th>
                <th className="px-3 py-2 text-right">Entry</th>
                <th className="px-3 py-2 text-right">Mark</th>
                <th className="px-3 py-2 text-right">P&amp;L $</th>
                <th className="px-3 py-2 text-right">P&amp;L %</th>
                <th className="px-3 py-2 text-right">DTE</th>
                <th className="px-3 py-2 text-right">Entry IV</th>
                <th className="px-3 py-2 text-right">Current IV</th>
                <th className="px-3 py-2 text-right">Delta</th>
                <th className="px-3 py-2 text-right">Gamma</th>
                <th className="px-3 py-2 text-right">Vega</th>
                <th className="px-3 py-2 text-right">Theta</th>
              </tr>
            </thead>
            <tbody>
              {currentPositions.map((pos, idx) => {
                const pnl = parseFloat(pos.unrealisedPnl || '0');
                const pnlPercent = formatPnlPercent(pos.unrealisedPnl, pos.avgPrice, pos.size);
                const dte = calculateDTE(pos.symbol);

                return (
                  <tr key={`${pos.symbol}-${idx}`} className="border-b border-gray-800 hover:bg-gray-800/40">
                    <td className="px-3 py-2 font-mono text-xs">{pos.symbol}</td>
                    <td className="px-3 py-2">
                      <span className={pos.side === 'Buy' ? 'text-success-600' : 'text-danger-600'}>
                        {pos.side}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right">{pos.size}</td>
                    <td className="px-3 py-2 text-right">{parseFloat(pos.avgPrice || '0').toFixed(2)}</td>
                    <td className="px-3 py-2 text-right">{parseFloat(pos.markPrice || '0').toFixed(2)}</td>
                    <td className={`px-3 py-2 text-right font-medium ${pnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                      {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
                    </td>
                    <td className={`px-3 py-2 text-right ${parseFloat(pnlPercent) >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                      {parseFloat(pnlPercent) >= 0 ? '+' : ''}{pnlPercent}%
                    </td>
                    <td className="px-3 py-2 text-right">{dte !== null ? `${dte}d` : '-'}</td>
                    <td className="px-3 py-2 text-right">
                      {pos.entry_iv !== null ? `${pos.entry_iv.toFixed(1)}%` : '-'}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {pos.current_iv ? `${(parseFloat(pos.current_iv) * 100).toFixed(1)}%` : '-'}
                    </td>
                    <td className="px-3 py-2 text-right">{pos.delta || '-'}</td>
                    <td className="px-3 py-2 text-right">{pos.gamma || '-'}</td>
                    <td className="px-3 py-2 text-right">{pos.vega || '-'}</td>
                    <td className="px-3 py-2 text-right">{pos.theta || '-'}</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot className="text-sm text-gray-300">
              <tr>
                <td colSpan={10} className="px-3 py-2 text-right font-medium">Aggregate Greeks:</td>
                <td className="px-3 py-2 text-right">{aggregateGreeks.delta.toFixed(4)}</td>
                <td className="px-3 py-2 text-right">{aggregateGreeks.gamma.toFixed(6)}</td>
                <td className="px-3 py-2 text-right">{aggregateGreeks.vega.toFixed(2)}</td>
                <td className="px-3 py-2 text-right">{aggregateGreeks.theta.toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        {currentPositions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No {activeTab} positions
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioTableV2;

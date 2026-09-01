import React from 'react';
import { Play, Pause, Edit, Trash2 } from 'lucide-react';
import type { AmmStrategy } from '../../types/amm';

interface StrategyCardProps {
    strategy: AmmStrategy;
    onEdit: (id: number) => void;
    onPause: (id: number) => void;
    onResume: (id: number) => void;
    onDelete: (id: number) => void;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
    strategy,
    onEdit,
    onPause,
    onResume,
    onDelete,
}) => {
    const isActive = strategy.status === 'ACTIVE';

    return (
        <div className={`bg-gray-900 rounded-lg border p-4 transition ${isActive ? 'border-green-500/30' : 'border-gray-700'
            }`}>
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h4 className="font-semibold text-white">{strategy.name}</h4>
                    <div className="flex items-center space-x-2 mt-1">
                        <span className="text-sm text-gray-400">{strategy.symbol}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${isActive
                                ? 'bg-green-900/30 text-green-400 border border-green-500/30'
                                : 'bg-gray-700 text-gray-400'
                            }`}>
                            {isActive ? '● ACTIVE' : '⏸ PAUSED'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Parameters Grid */}
            <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-gray-800 rounded p-2">
                    <div className="text-xs text-gray-500">Skew Factor</div>
                    <div className="text-sm font-mono font-semibold text-white mt-0.5">
                        {strategy.skew_factor.toFixed(2)}
                    </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                    <div className="text-xs text-gray-500">Spread</div>
                    <div className="text-sm font-mono font-semibold text-white mt-0.5">
                        {strategy.spread_bps} bps
                    </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                    <div className="text-xs text-gray-500">Min IV</div>
                    <div className="text-sm font-mono font-semibold text-white mt-0.5">
                        {(strategy.min_iv * 100).toFixed(0)}%
                    </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                    <div className="text-xs text-gray-500">Max IV</div>
                    <div className="text-sm font-mono font-semibold text-white mt-0.5">
                        {(strategy.max_iv * 100).toFixed(0)}%
                    </div>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2">
                <button
                    onClick={() => onEdit(strategy.id)}
                    className="flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition"
                    title="Edit Strategy"
                >
                    <Edit className="w-3.5 h-3.5" />
                    <span>Edit</span>
                </button>
                {isActive ? (
                    <button
                        onClick={() => onPause(strategy.id)}
                        className="flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm font-medium transition"
                        title="Pause Strategy"
                    >
                        <Pause className="w-3.5 h-3.5" />
                        <span>Pause</span>
                    </button>
                ) : (
                    <button
                        onClick={() => onResume(strategy.id)}
                        className="flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium transition"
                        title="Resume Strategy"
                    >
                        <Play className="w-3.5 h-3.5" />
                        <span>Resume</span>
                    </button>
                )}
                <button
                    onClick={() => onDelete(strategy.id)}
                    className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm font-medium transition border border-red-500/30"
                    title="Delete Strategy"
                >
                    <Trash2 className="w-3.5 h-3.5" />
                </button>
            </div>

            {/* Timestamps */}
            <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-gray-500">
                <div>Created: {new Date(strategy.created_at).toLocaleDateString()}</div>
                <div>Updated: {new Date(strategy.updated_at).toLocaleDateString()}</div>
            </div>
        </div>
    );
};

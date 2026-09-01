import React, { useEffect, useState } from 'react';
import { Plus, RefreshCw } from 'lucide-react';
import ammApi from '../../services/ammApi';
import type { AmmStrategy } from '../../types/amm';
import { StrategyCard } from './StrategyCard';
import { LoadingSpinner } from '../Common/LoadingSpinner';

interface StrategyListProps {
    onCreateNew: () => void;
}

export const StrategyList: React.FC<StrategyListProps> = ({ onCreateNew }) => {
    const [strategies, setStrategies] = useState<AmmStrategy[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStrategies = async () => {
        try {
            setError(null);
            const data = await ammApi.getStrategies();
            setStrategies(data.strategies || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch strategies');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStrategies();
    }, []);

    const handleEdit = (id: number) => {
        // TODO: Implement edit modal
        console.log('Edit strategy:', id);
    };

    const handlePause = async (id: number) => {
        try {
            await ammApi.pauseStrategy(id);
            await fetchStrategies();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to pause strategy');
        }
    };

    const handleResume = async (id: number) => {
        try {
            await ammApi.resumeStrategy(id);
            await fetchStrategies();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to resume strategy');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this strategy?')) return;

        try {
            // TODO: Implement delete endpoint
            console.log('Delete strategy:', id);
            await fetchStrategies();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete strategy');
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">AMM Strategies</h3>
                <div className="flex space-x-2">
                    <button
                        onClick={fetchStrategies}
                        className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm font-medium transition flex items-center space-x-1"
                    >
                        <RefreshCw className="w-4 h-4" />
                        <span>Refresh</span>
                    </button>
                    <button
                        onClick={onCreateNew}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition flex items-center space-x-1"
                    >
                        <Plus className="w-4 h-4" />
                        <span>New Strategy</span>
                    </button>
                </div>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-md text-red-400 text-sm">
                    {error}
                </div>
            )}

            {loading ? (
                <LoadingSpinner size="sm" text="Loading strategies..." />
            ) : strategies.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                    <p>No strategies found</p>
                    <button
                        onClick={onCreateNew}
                        className="mt-3 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition"
                    >
                        Create Your First Strategy
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {strategies.map((strategy) => (
                        <StrategyCard
                            key={strategy.id}
                            strategy={strategy}
                            onEdit={handleEdit}
                            onPause={handlePause}
                            onResume={handleResume}
                            onDelete={handleDelete}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

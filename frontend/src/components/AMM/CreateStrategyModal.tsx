import React, { useState } from 'react';
import { X } from 'lucide-react';
import ammApi from '../../services/ammApi';
import type { CreateStrategyRequest } from '../../types/amm';

interface CreateStrategyModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const CreateStrategyModal: React.FC<CreateStrategyModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [formData, setFormData] = useState<CreateStrategyRequest>({
        name: '',
        symbol: 'BTC',
        skew_factor: 1.0,
        spread_bps: 10,
        min_iv: 0.3,
        max_iv: 1.5,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await ammApi.createStrategy(formData);
            onSuccess();
            onClose();
            // Reset form
            setFormData({
                name: '',
                symbol: 'BTC',
                skew_factor: 1.0,
                spread_bps: 10,
                min_iv: 0.3,
                max_iv: 1.5,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create strategy');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 max-w-md w-full mx-4">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold">Create New Strategy</h3>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-700 rounded transition"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-md text-red-400 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">
                            Strategy Name *
                        </label>
                        <input
                            type="text"
                            required
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                            placeholder="e.g., BTC Main Strategy"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">
                            Symbol *
                        </label>
                        <select
                            value={formData.symbol}
                            onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                        >
                            <option value="BTC">BTC</option>
                            <option value="ETH">ETH</option>
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Skew Factor
                            </label>
                            <input
                                type="number"
                                step="0.01"
                                min="0.5"
                                max="2.0"
                                value={formData.skew_factor}
                                onChange={(e) => setFormData({ ...formData, skew_factor: parseFloat(e.target.value) })}
                                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Spread (bps)
                            </label>
                            <input
                                type="number"
                                min="5"
                                max="100"
                                value={formData.spread_bps}
                                onChange={(e) => setFormData({ ...formData, spread_bps: parseInt(e.target.value) })}
                                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Min IV
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0.1"
                                max="3.0"
                                value={formData.min_iv}
                                onChange={(e) => setFormData({ ...formData, min_iv: parseFloat(e.target.value) })}
                                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Max IV
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0.1"
                                max="3.0"
                                value={formData.max_iv}
                                onChange={(e) => setFormData({ ...formData, max_iv: parseFloat(e.target.value) })}
                                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                    </div>

                    <div className="flex space-x-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded font-medium transition"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition disabled:opacity-50"
                        >
                            {loading ? 'Creating...' : 'Create Strategy'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

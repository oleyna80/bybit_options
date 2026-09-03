import React, { useEffect, useState } from 'react';
import { Play, Square, Settings } from 'lucide-react';
import ammApi from '../../services/ammApi';
import type { EngineStatus } from '../../types/amm';
import { LoadingSpinner } from '../Common/LoadingSpinner';

export const EngineControl: React.FC = () => {
    const [status, setStatus] = useState<EngineStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = async () => {
        try {
            setError(null);
            const data = await ammApi.getEngineStatus();
            setStatus(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch status');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000); // Refresh every 5s
        return () => clearInterval(interval);
    }, []);

    const handleStart = async () => {
        setActionLoading(true);
        try {
            await ammApi.startEngine();
            await fetchStatus();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start engine');
        } finally {
            setActionLoading(false);
        }
    };

    const handleStop = async () => {
        setActionLoading(true);
        try {
            await ammApi.stopEngine();
            await fetchStatus();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to stop engine');
        } finally {
            setActionLoading(false);
        }
    };

    const handleModeChange = async (mode: 'MANUAL' | 'AUTO') => {
        setActionLoading(true);
        try {
            await ammApi.setMode(mode);
            await fetchStatus();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to change mode');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <LoadingSpinner size="sm" text="Loading engine status..." />
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center">
                    <Settings className="w-5 h-5 mr-2 text-blue-400" />
                    Engine Control
                </h3>
                {status && (
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${status.is_running
                            ? 'bg-green-900/20 text-green-400 border border-green-500/30'
                            : 'bg-gray-700 text-gray-400 border border-gray-600'
                        }`}>
                        {status.is_running ? '● RUNNING' : '○ STOPPED'}
                    </div>
                )}
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-md text-red-400 text-sm">
                    {error}
                </div>
            )}

            {status && (
                <div className="space-y-4">
                    {/* Control Buttons */}
                    <div className="flex space-x-2">
                        <button
                            onClick={handleStart}
                            disabled={status.is_running || actionLoading}
                            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md font-medium transition ${status.is_running || actionLoading
                                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                    : 'bg-green-600 hover:bg-green-700 text-white'
                                }`}
                        >
                            <Play className="w-4 h-4" />
                            <span>Start</span>
                        </button>
                        <button
                            onClick={handleStop}
                            disabled={!status.is_running || actionLoading}
                            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md font-medium transition ${!status.is_running || actionLoading
                                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                    : 'bg-red-600 hover:bg-red-700 text-white'
                                }`}
                        >
                            <Square className="w-4 h-4" />
                            <span>Stop</span>
                        </button>
                    </div>

                    {/* Mode Selector */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">
                            Operating Mode
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={() => handleModeChange('MANUAL')}
                                disabled={actionLoading}
                                className={`px-4 py-2 rounded-md font-medium transition ${status.mode === 'MANUAL'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                            >
                                Manual
                            </button>
                            <button
                                onClick={() => handleModeChange('AUTO')}
                                disabled={actionLoading}
                                className={`px-4 py-2 rounded-md font-medium transition ${status.mode === 'AUTO'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                            >
                                Auto
                            </button>
                        </div>
                    </div>

                    {/* Last Cycle */}
                    {status.last_cycle_at && (
                        <div className="pt-3 border-t border-gray-700">
                            <div className="text-xs text-gray-400">Last Cycle</div>
                            <div className="text-sm font-mono text-gray-300 mt-1">
                                {new Date(status.last_cycle_at).toLocaleString()}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

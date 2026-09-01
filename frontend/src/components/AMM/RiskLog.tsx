import React, { useEffect, useState } from 'react';
import { Shield, CheckCircle, XCircle } from 'lucide-react';
import ammApi from '../../services/ammApi';
import type { RiskDecision } from '../../types/amm';
import { LoadingSpinner } from '../Common/LoadingSpinner';

export const RiskLog: React.FC = () => {
    const [decisions, setDecisions] = useState<RiskDecision[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchDecisions = async () => {
        try {
            setError(null);
            const data = await ammApi.getRiskDecisions(50);
            setDecisions(data.decisions || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch risk decisions');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDecisions();
        const interval = setInterval(fetchDecisions, 15000); // Refresh every 15s
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <LoadingSpinner size="sm" text="Loading risk decisions..." />
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center">
                    <Shield className="w-5 h-5 mr-2 text-blue-400" />
                    Risk Decisions Log
                </h3>
                <span className="text-sm text-gray-400">Last 50 decisions</span>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-md text-red-400 text-sm">
                    {error}
                </div>
            )}

            {decisions.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                    No risk decisions yet
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-gray-700">
                                <th className="text-left py-2 px-3 text-gray-400 font-medium">Time</th>
                                <th className="text-left py-2 px-3 text-gray-400 font-medium">Type</th>
                                <th className="text-left py-2 px-3 text-gray-400 font-medium">Decision</th>
                                <th className="text-left py-2 px-3 text-gray-400 font-medium">Reason</th>
                                <th className="text-left py-2 px-3 text-gray-400 font-medium">Strategy</th>
                            </tr>
                        </thead>
                        <tbody>
                            {decisions.map((decision) => (
                                <tr key={decision.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                    <td className="py-2 px-3 font-mono text-xs text-gray-400">
                                        {new Date(decision.timestamp).toLocaleTimeString()}
                                    </td>
                                    <td className="py-2 px-3">
                                        <span className="px-2 py-0.5 bg-gray-700 rounded text-xs">
                                            {decision.decision_type}
                                        </span>
                                    </td>
                                    <td className="py-2 px-3">
                                        {decision.approved ? (
                                            <span className="flex items-center text-green-400">
                                                <CheckCircle className="w-4 h-4 mr-1" />
                                                APPROVED
                                            </span>
                                        ) : (
                                            <span className="flex items-center text-red-400">
                                                <XCircle className="w-4 h-4 mr-1" />
                                                REJECTED
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-2 px-3 text-gray-300">{decision.reason}</td>
                                    <td className="py-2 px-3 text-gray-400">
                                        {decision.strategy_id ? `#${decision.strategy_id}` : '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

import React, { useEffect, useState } from 'react';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import ammApi from '../../services/ammApi';
import type { PortfolioGreeksData } from '../../types/amm';
import { LoadingSpinner } from '../Common/LoadingSpinner';

interface GreekGaugeProps {
    label: string;
    value: number;
    target?: number;
    min: number;
    max: number;
    unit?: string;
    colorScheme: 'delta' | 'positive' | 'negative';
}

const GreekGauge: React.FC<GreekGaugeProps> = ({ label, value, target, min, max, unit = '', colorScheme }) => {
    // Calculate percentage for progress bar
    const range = max - min;
    const percentage = ((value - min) / range) * 100;
    const clampedPercentage = Math.max(0, Math.min(100, percentage));

    // Determine color based on scheme and value
    let barColor = 'bg-blue-500';
    let textColor = 'text-blue-400';

    if (colorScheme === 'delta') {
        if (Math.abs(value) < 0.1) {
            barColor = 'bg-green-500';
            textColor = 'text-green-400';
        } else if (Math.abs(value) < 0.3) {
            barColor = 'bg-yellow-500';
            textColor = 'text-yellow-400';
        } else {
            barColor = 'bg-red-500';
            textColor = 'text-red-400';
        }
    } else if (colorScheme === 'positive') {
        barColor = 'bg-green-500';
        textColor = 'text-green-400';
    } else if (colorScheme === 'negative') {
        barColor = 'bg-red-500';
        textColor = 'text-red-400';
    }

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-400">{label}</span>
                <span className={`text-lg font-mono font-semibold ${textColor}`}>
                    {value >= 0 ? '+' : ''}{value.toFixed(2)}{unit}
                </span>
            </div>
            <div className="relative h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                    className={`absolute left-0 top-0 h-full ${barColor} transition-all duration-300`}
                    style={{ width: `${clampedPercentage}%` }}
                />
                {target !== undefined && (
                    <div
                        className="absolute top-0 w-0.5 h-full bg-white opacity-50"
                        style={{ left: `${((target - min) / range) * 100}%` }}
                    />
                )}
            </div>
            <div className="flex justify-between text-xs text-gray-500 font-mono">
                <span>{min.toFixed(1)}</span>
                <span>{max.toFixed(1)}</span>
            </div>
        </div>
    );
};

export const PortfolioGreeks: React.FC = () => {
    const [greeks, setGreeks] = useState<PortfolioGreeksData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchGreeks = async () => {
        try {
            setError(null);
            const data = await ammApi.getPortfolioGreeks();
            setGreeks(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch Greeks');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchGreeks();
        const interval = setInterval(fetchGreeks, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <LoadingSpinner size="sm" text="Loading portfolio Greeks..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <div className="text-red-400 text-sm">{error}</div>
            </div>
        );
    }

    if (!greeks) {
        return null;
    }

    // Determine overall risk status
    const deltaRisk = Math.abs(greeks.delta);
    let riskStatus: 'low' | 'medium' | 'high' = 'low';
    let riskColor = 'text-green-400';
    let riskBg = 'bg-green-900/20 border-green-500/30';

    if (deltaRisk > 0.3) {
        riskStatus = 'high';
        riskColor = 'text-red-400';
        riskBg = 'bg-red-900/20 border-red-500/30';
    } else if (deltaRisk > 0.1) {
        riskStatus = 'medium';
        riskColor = 'text-yellow-400';
        riskBg = 'bg-yellow-900/20 border-yellow-500/30';
    }

    return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center">
                    <Activity className="w-5 h-5 mr-2 text-blue-400" />
                    Portfolio Greeks
                </h3>
                <div className={`px-3 py-1 rounded-full text-xs font-medium border ${riskBg} ${riskColor}`}>
                    {riskStatus.toUpperCase()} RISK
                </div>
            </div>

            <div className="space-y-4">
                {/* Delta - Most Important */}
                <GreekGauge
                    label="Delta (Directional Exposure)"
                    value={greeks.delta}
                    target={0}
                    min={-1.0}
                    max={1.0}
                    colorScheme="delta"
                />

                {/* Gamma */}
                <GreekGauge
                    label="Gamma (Delta Sensitivity)"
                    value={greeks.gamma}
                    min={0}
                    max={500}
                    colorScheme="positive"
                />

                {/* Vega */}
                <GreekGauge
                    label="Vega (IV Sensitivity)"
                    value={greeks.vega}
                    min={-200}
                    max={200}
                    colorScheme="positive"
                />

                {/* Theta */}
                <GreekGauge
                    label="Theta (Time Decay)"
                    value={greeks.theta}
                    min={-50}
                    max={0}
                    unit="/day"
                    colorScheme="negative"
                />
            </div>

            {/* Timestamp */}
            <div className="mt-4 pt-3 border-t border-gray-700">
                <div className="text-xs text-gray-400">Last Updated</div>
                <div className="text-sm font-mono text-gray-300 mt-1">
                    {new Date(greeks.timestamp).toLocaleString()}
                </div>
            </div>

            {/* Delta Interpretation */}
            <div className="mt-3 p-3 bg-gray-900/50 rounded-md">
                <div className="flex items-center text-sm">
                    {greeks.delta > 0.1 ? (
                        <>
                            <TrendingUp className="w-4 h-4 mr-2 text-green-400" />
                            <span className="text-gray-300">
                                <span className="text-green-400 font-semibold">Bullish</span> exposure - profits from price increase
                            </span>
                        </>
                    ) : greeks.delta < -0.1 ? (
                        <>
                            <TrendingDown className="w-4 h-4 mr-2 text-red-400" />
                            <span className="text-gray-300">
                                <span className="text-red-400 font-semibold">Bearish</span> exposure - profits from price decrease
                            </span>
                        </>
                    ) : (
                        <>
                            <Minus className="w-4 h-4 mr-2 text-gray-400" />
                            <span className="text-gray-300">
                                <span className="text-gray-400 font-semibold">Neutral</span> - delta-hedged position
                            </span>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

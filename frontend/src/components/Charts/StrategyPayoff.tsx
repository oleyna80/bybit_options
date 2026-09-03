import React from 'react';
import { ResponsiveContainer, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Area } from 'recharts';

export const StrategyPayoff: React.FC = () => {
    // Mock data for payoff
    const data = Array.from({ length: 41 }, (_, i) => {
        const price = 80000 + i * 1000;
        // Simple butterfly spread logic mock
        const profit = Math.max(0, price - 90000) - 2 * Math.max(0, price - 95000) + Math.max(0, price - 100000) - 500;
        return {
            price,
            expiry: profit,
            current: profit * 0.6 // Simplified curve for current time
        };
    });

    return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-[400px]">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Strategy P&L (Payoff)</h3>
                <div className="flex space-x-2 text-xs">
                    <span className="flex items-center text-blue-400"><div className="w-2 h-2 bg-blue-400 rounded-full mr-1" /> Expiry</span>
                    <span className="flex items-center text-gray-300"><div className="w-2 h-2 bg-gray-300 rounded-full mr-1" /> Now</span>
                </div>
            </div>

            <div className="h-[320px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis
                            dataKey="price"
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF', fontSize: 10 }}
                            tickFormatter={(val) => `${val / 1000}k`}
                            minTickGap={30}
                        />
                        <YAxis
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF', fontSize: 10 }}
                            tickFormatter={(val) => `$${val}`}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                            itemStyle={{ color: '#F3F4F6' }}
                            labelFormatter={(label) => `Price: $${label}`}
                        />
                        <ReferenceLine y={0} stroke="#4B5563" />

                        <Area type="monotone" dataKey="expiry" fill="url(#colorExpiry)" stroke="none" fillOpacity={0.1} />

                        <Line
                            type="monotone"
                            dataKey="expiry"
                            stroke="#60A5FA"
                            strokeWidth={2}
                            dot={false}
                            name="At Expiry"
                        />
                        <Line
                            type="monotone"
                            dataKey="current"
                            stroke="#E5E7EB"
                            strokeWidth={2}
                            dot={false}
                            strokeDasharray="5 5"
                            name="Current"
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

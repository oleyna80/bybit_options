import React from 'react';

export const GreeksOverview: React.FC = () => {
    // Mock Greeks data
    const greeks = [
        { label: 'Delta', value: '-15.20', unit: 'BTC', sentiment: 'Short', color: 'text-red-400' },
        { label: 'Gamma', value: '+0.82', unit: 'per 1%', sentiment: 'Long', color: 'text-green-400' },
        { label: 'Theta', value: '+$85.00', unit: 'per day', sentiment: 'income', color: 'text-green-400' },
        { label: 'Vega', value: '-420.00', unit: 'per 1% IV', sentiment: 'Short Vol', color: 'text-red-400' },
    ];

    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            {greeks.map((greek) => (
                <div key={greek.label} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                    <div className="text-xs text-gray-400 mb-1">{greek.label}</div>
                    <div className={`text-xl font-bold ${greek.color}`}>{greek.value}</div>
                    <div className="flex justify-between items-center mt-1">
                        <span className="text-[10px] text-gray-500">{greek.unit}</span>
                        <span className="text-[10px] bg-gray-700 px-1 rounded text-gray-300">{greek.sentiment}</span>
                    </div>
                </div>
            ))}
        </div>
    );
};

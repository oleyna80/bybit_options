import React from 'react';
import { Wifi, WifiOff, Clock, Server } from 'lucide-react';

interface FooterProps {
    isConnected: boolean;
    lastUpdate: Date | null;
    onReconnect: () => void;
}

export const Footer: React.FC<FooterProps> = ({
    isConnected,
    lastUpdate,
    onReconnect
}) => {
    return (
        <footer className="bg-gray-900 border-t border-gray-800 py-3 px-6 mt-auto">
            <div className="max-w-[1920px] mx-auto flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2">
                        <span className="font-semibold text-gray-400">Bybit Options Risk Engine</span>
                        <span className="px-1.5 py-0.5 bg-gray-800 rounded text-[10px]">v1.0.0</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <Server className="w-3 h-3" />
                        <span>Environment: <span className="text-gray-400">Production (WSL)</span></span>
                    </div>
                </div>

                <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2" title="Last Data Update">
                        <Clock className="w-3 h-3" />
                        <span>Updated: <span className="font-mono text-gray-400">
                            {lastUpdate ? lastUpdate.toLocaleTimeString() : '--:--:--'}
                        </span></span>
                    </div>

                    <div className="flex items-center space-x-3">
                        <div className={`flex items-center space-x-1.5 ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
                            {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                            <span className="font-medium">{isConnected ? 'WS Connected' : 'Disconnected'}</span>
                        </div>

                        {!isConnected && (
                            <button
                                onClick={onReconnect}
                                className="px-2 py-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded transition-colors"
                            >
                                Reconnect
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </footer>
    );
};

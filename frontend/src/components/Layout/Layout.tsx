import React from 'react';
import { Header, TabId } from './Header';
import { Footer } from './Footer';

interface LayoutProps {
    children: React.ReactNode;
    activeTab: TabId;
    onTabChange: (tab: TabId) => void;
    isConnected: boolean;
    onReconnect: () => void;
    onExportJson?: () => void;
    onExportMd?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
    children,
    activeTab,
    onTabChange,
    isConnected,
    onReconnect,
    onExportJson,
    onExportMd
}) => {
    return (
        <div className="min-h-screen bg-[#0B0E14] text-gray-100 flex flex-col font-sans selection:bg-blue-500/30">
            <Header
                activeTab={activeTab}
                onTabChange={onTabChange}
                onExportJson={onExportJson}
                onExportMd={onExportMd}
            />

            <main className="flex-1 p-6 relative">
                <div className="max-w-[1920px] mx-auto space-y-6">
                    {children}
                </div>
            </main>

            <Footer
                isConnected={isConnected}
                lastUpdate={new Date()} // In real app, pass actual time
                onReconnect={onReconnect}
            />
        </div>
    );
};

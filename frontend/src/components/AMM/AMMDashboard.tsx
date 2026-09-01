import React, { useState } from 'react';
import { EngineControl } from './EngineControl';
import { PortfolioGreeks } from './PortfolioGreeks';
import { StrategyList } from './StrategyList';
import { RiskLog } from './RiskLog';
import { CreateStrategyModal } from './CreateStrategyModal';

export const AMMDashboard: React.FC = () => {
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);

    const handleCreateSuccess = () => {
        setRefreshKey(prev => prev + 1); // Trigger refresh of strategy list
    };

    return (
        <div className="space-y-6">
            {/* Top Row: Engine Control + Portfolio Greeks */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <EngineControl />
                <PortfolioGreeks />
            </div>

            {/* Strategy List */}
            <StrategyList
                key={refreshKey}
                onCreateNew={() => setIsCreateModalOpen(true)}
            />

            {/* Risk Decisions Log */}
            <RiskLog />

            {/* Create Strategy Modal */}
            <CreateStrategyModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSuccess={handleCreateSuccess}
            />
        </div>
    );
};

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Shield, Zap, BarChart3 } from 'lucide-react';
import apiClient from '../../services/api';
import { PortfolioRiskModel } from '../../types';

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  className?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  icon,
  trend = 'neutral',
  description,
  className = '',
}) => {
  const trendColors = {
    up: 'text-success-600',
    down: 'text-danger-600',
    neutral: 'text-muted-foreground',
  };

  const trendIcons = {
    up: <TrendingUp className="h-4 w-4" />,
    down: <TrendingDown className="h-4 w-4" />,
    neutral: null,
  };

  return (
    <div className={`metric-card p-6 ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              {icon}
            </div>
            <h3 className="font-semibold">{title}</h3>
          </div>
          <div className="text-3xl font-bold mt-2">{value}</div>
          {change && (
            <div className={`flex items-center gap-1 mt-2 ${trendColors[trend]}`}>
              {trendIcons[trend]}
              <span className="text-sm font-medium">{change}</span>
            </div>
          )}
          {description && (
            <p className="text-sm text-muted-foreground mt-3">{description}</p>
          )}
        </div>
      </div>
    </div>
  );
};

interface MetricsCardsProps {
  // Props for external control (optional)
  isLoading?: boolean;
  error?: string | null;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({
  isLoading: externalLoading = false,
  error: externalError = null,
}) => {
  const [portfolioData, setPortfolioData] = useState<PortfolioRiskModel | null>(null);
  const [internalLoading, setInternalLoading] = useState<boolean>(true);
  const [internalError, setInternalError] = useState<string | null>(null);

  // Load portfolio data from API
  useEffect(() => {
    const loadPortfolioData = async () => {
      try {
        setInternalLoading(true);
        setInternalError(null);
        
        const response = await apiClient.getPortfolio();
        
        if (response.success) {
          setPortfolioData(response.data);
        } else {
          setInternalError('Failed to load portfolio data');
        }
      } catch (err: any) {
        setInternalError(err.message || 'Network error');
        console.error('Error loading portfolio data:', err);
      } finally {
        setInternalLoading(false);
      }
    };

    loadPortfolioData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadPortfolioData, 30000);
    return () => clearInterval(interval);
  }, []);

  const displayLoading = externalLoading || internalLoading;
  const displayError = externalError || internalError;

  // Use real data if available, otherwise use defaults
  const totalEquity = portfolioData?.margin?.total_equity || 0;
  const marginUtilization = portfolioData?.margin?.margin_ratio || 0;
  const totalDelta = portfolioData?.coin_risks?.BTC?.total_greeks?.delta_coin || 0;
  const totalTheta = portfolioData?.total_theta_usd || 0;
  const totalVega = portfolioData?.total_vega_usd || 0;
  const totalGamma = portfolioData?.coin_risks?.BTC?.total_greeks?.gamma_coin || 0;

  if (displayError) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="metric-card p-6 border-danger-200 bg-danger-50">
          <div className="text-danger-600 font-semibold">Error loading metrics</div>
          <div className="text-sm text-danger-500 mt-2">{displayError}</div>
        </div>
      </div>
    );
  }

  if (displayLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="metric-card p-6">
            <div className="animate-pulse">
              <div className="h-4 bg-muted rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-muted rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-muted rounded w-1/3"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const deltaTrend: 'up' | 'down' | 'neutral' = totalDelta > 0.1 ? 'up' : totalDelta < -0.1 ? 'down' : 'neutral';
  const thetaTrend: 'up' | 'down' | 'neutral' = totalTheta > 0 ? 'up' : 'down';
  const marginTrend: 'up' | 'down' | 'neutral' = marginUtilization > 70 ? 'down' : marginUtilization > 50 ? 'neutral' : 'up';

  const deltaInterpretation = Math.abs(totalDelta) < 0.1
    ? 'Delta neutral portfolio'
    : totalDelta > 0
      ? `Long ${totalDelta.toFixed(4)} BTC equivalent`
      : `Short ${Math.abs(totalDelta).toFixed(4)} BTC equivalent`;

  const thetaInterpretation = totalTheta > 0
    ? 'Earning time decay'
    : `Paying $${Math.abs(totalTheta).toFixed(2)}/day in theta`;

  const marginInterpretation = marginUtilization < 50
    ? 'Healthy margin utilization'
    : marginUtilization < 75
      ? 'Moderate margin usage'
      : 'High margin risk';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <MetricCard
        title="Total Equity"
        value={`$${totalEquity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        change={`${marginUtilization.toFixed(1)}% margin used`}
        icon={<DollarSign className="h-5 w-5" />}
        trend={marginTrend}
        description={marginInterpretation}
        className={marginUtilization > 70 ? 'metric-card-negative' : marginUtilization > 50 ? '' : 'metric-card-positive'}
      />
      
      <MetricCard
        title="Portfolio Delta"
        value={totalDelta.toFixed(4)}
        change={deltaInterpretation}
        icon={<TrendingUp className="h-5 w-5" />}
        trend={deltaTrend}
        description={Math.abs(totalDelta) < 0.1 ? 'Neutral position' : totalDelta > 0 ? 'Bullish exposure' : 'Bearish exposure'}
        className={Math.abs(totalDelta) < 0.1 ? 'metric-card-neutral' : totalDelta > 0 ? 'metric-card-positive' : 'metric-card-negative'}
      />
      
      <MetricCard
        title="Daily Theta"
        value={`$${Math.abs(totalTheta).toFixed(2)}/day`}
        change={thetaInterpretation}
        icon={<Zap className="h-5 w-5" />}
        trend={thetaTrend}
        description={totalTheta > 0 ? 'Positive theta (earning)' : 'Negative theta (cost)'}
        className={totalTheta > 0 ? 'metric-card-positive' : 'metric-card-negative'}
      />
      
      <MetricCard
        title="Vega Exposure"
        value={`$${totalVega.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        change="Volatility sensitivity"
        icon={<BarChart3 className="h-5 w-5" />}
        trend="neutral"
        description={totalVega > 0 ? 'Long volatility' : totalVega < 0 ? 'Short volatility' : 'Neutral to volatility'}
        className={totalVega > 1000 ? 'metric-card-positive' : totalVega < -1000 ? 'metric-card-negative' : 'metric-card-neutral'}
      />
      
      <MetricCard
        title="Gamma Exposure"
        value={totalGamma.toFixed(6)}
        change="Curvature risk"
        icon={<Shield className="h-5 w-5" />}
        trend="neutral"
        description={totalGamma > 0 ? 'Positive gamma (convex)' : totalGamma < 0 ? 'Negative gamma (concave)' : 'Flat gamma'}
        className={Math.abs(totalGamma) > 0.001 ? 'metric-card-positive' : 'metric-card-neutral'}
      />
      
      <MetricCard
        title="Risk Status"
        value={marginUtilization > 70 ? "High Risk" : marginUtilization > 50 ? "Moderate" : "Low Risk"}
        change={`${marginUtilization.toFixed(1)}% margin`}
        icon={<Shield className="h-5 w-5" />}
        trend={marginTrend}
        description={marginUtilization > 70 ? 'Consider reducing exposure' : marginUtilization > 50 ? 'Monitor closely' : 'Within safe limits'}
        className={marginUtilization > 70 ? 'metric-card-negative' : marginUtilization > 50 ? '' : 'metric-card-positive'}
      />
    </div>
  );
};
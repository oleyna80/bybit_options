"""Backward-compatible re-exports for Pydantic models."""

from bybit_options.models import (
    PositionSide,
    PositionType,
    OptionType,
    CoinHolding,
    GreeksModel,
    SlippageMetrics,
    IVMetrics,
    GammaRentMetrics,
    PositionModel,
    CoinRiskModel,
    MarginModel,
    PortfolioRiskModel,
    PerpetualOHLCV,
    OptionIVDaily,
    IVRankDaily,
    PriceHistoryResponse,
    IVHistoryResponse,
    IVRankHistoryResponse,
)

try:
    from strategy_models import (
        StrategyType,
        IronCondorLeg,
        IronCondorConfig,
        HedgeInstrument,
        HedgeRecommendation,
        ScenarioParameters,
        ScenarioResult,
        AnalysisResult,
        ExportFormat,
        ExportRequest,
    )
except ImportError:
    class StrategyType:
        pass

    class IronCondorLeg:
        pass

    class IronCondorConfig:
        pass

    class HedgeInstrument:
        pass

    class HedgeRecommendation:
        pass

    class ScenarioParameters:
        pass

    class ScenarioResult:
        pass

    class AnalysisResult:
        pass

    class ExportFormat:
        pass

    class ExportRequest:
        pass


__all__ = [
    "PositionSide",
    "PositionType",
    "OptionType",
    "CoinHolding",
    "GreeksModel",
    "SlippageMetrics",
    "IVMetrics",
    "GammaRentMetrics",
    "PositionModel",
    "CoinRiskModel",
    "MarginModel",
    "PortfolioRiskModel",
    "PerpetualOHLCV",
    "OptionIVDaily",
    "IVRankDaily",
    "PriceHistoryResponse",
    "IVHistoryResponse",
    "IVRankHistoryResponse",
    "StrategyType",
    "IronCondorLeg",
    "IronCondorConfig",
    "HedgeInstrument",
    "HedgeRecommendation",
    "ScenarioParameters",
    "ScenarioResult",
    "AnalysisResult",
    "ExportFormat",
    "ExportRequest",
]

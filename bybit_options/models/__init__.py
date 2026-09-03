"""Pydantic models for the risk engine."""

from bybit_options.models.greeks import GreeksModel, SlippageMetrics, IVMetrics, GammaRentMetrics
from bybit_options.models.positions import PositionSide, PositionType, OptionType, PositionModel
from bybit_options.models.portfolio import CoinHolding, CoinRiskModel, MarginModel, PortfolioRiskModel
from bybit_options.models.market_data import (
    PerpetualOHLCV,
    OptionIVDaily,
    IVRankDaily,
    PriceHistoryResponse,
    IVHistoryResponse,
    IVRankHistoryResponse,
    OptionBoardOption,
    OptionsBoardResponse,
)
from bybit_options.models.trade_history import (
    ExecutionRecord,
    ExecutionHistoryResult,
    ExecutionHistoryResponse,
    OrderRecord,
    OrderHistoryResult,
    OrderHistoryResponse,
)

__all__ = [
    "GreeksModel",
    "SlippageMetrics",
    "IVMetrics",
    "GammaRentMetrics",
    "PositionSide",
    "PositionType",
    "OptionType",
    "PositionModel",
    "CoinHolding",
    "CoinRiskModel",
    "MarginModel",
    "PortfolioRiskModel",
    "PerpetualOHLCV",
    "OptionIVDaily",
    "IVRankDaily",
    "PriceHistoryResponse",
    "IVHistoryResponse",
    "IVRankHistoryResponse",
    "OptionBoardOption",
    "OptionsBoardResponse",
    "ExecutionRecord",
    "ExecutionHistoryResult",
    "ExecutionHistoryResponse",
    "OrderRecord",
    "OrderHistoryResult",
    "OrderHistoryResponse",
]

# Delta Analytics models
from .delta_models import (
    LargeTradeModel,
    OrderbookSnapshotModel,
    OrderbookLevel,
    DeltaMetricsModel
)

__all__.extend([
    "LargeTradeModel",
    "OrderbookSnapshotModel",
    "OrderbookLevel",
    "DeltaMetricsModel"
])

"""
Strategy-specific configuration (extends main config.py)
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class StrategyConfig(BaseSettings):
    """Sigma-Fractal Strategy Parameters"""

    # Deribit API
    deribit_base_url: str = Field(
        default="https://www.deribit.com/api/v2",
        description="Deribit API base URL",
    )

    # Bollinger Bands
    bb_period: int = Field(default=20, description="BB period (20 days)")
    bb_std_inner: float = Field(default=1.0, description="Inner band (1σ)")
    bb_std_outer: float = Field(default=2.0, description="Outer band (2σ)")

    # Squeeze Detection
    squeeze_percentile: int = Field(
        default=25,
        description="BB Width percentile for squeeze (25th = tight)",
        ge=1,
        le=100,
    )

    # Williams Fractals
    fractal_bars: int = Field(
        default=5,
        description="Bars for fractal pattern (5-bar Williams)",
    )

    # DTE Ranges
    dte_core_min: int = Field(default=20, description="Min DTE for IC")
    dte_core_max: int = Field(default=35, description="Max DTE for IC")
    dte_hedge_min: int = Field(default=60, description="Min DTE for hedge")
    dte_hedge_max: int = Field(default=90, description="Max DTE for hedge")

    # Strike Selection (Delta targets)
    ic_put_delta: float = Field(default=-0.15, description="IC short put delta")
    ic_call_delta: float = Field(default=0.15, description="IC short call delta")

    # Cat Ears
    cat_ears_qty_ratio: float = Field(
        default=0.10,
        description="Cat Ears qty as % of main position",
    )
    cat_ears_gamma_threshold: float = Field(
        default=0.0005,
        description="Gamma threshold to trigger Cat Ears",
    )

    # Data Collection
    collection_interval_minutes: int = Field(
        default=60,
        description="How often to collect data (hourly)",
    )

    class Config:
        env_prefix = "STRATEGY_"


_strategy_config = None


def get_strategy_config() -> StrategyConfig:
    """Get strategy configuration singleton"""
    global _strategy_config
    if _strategy_config is None:
        _strategy_config = StrategyConfig()
    return _strategy_config


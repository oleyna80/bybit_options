"""
Delta Hedger Bot - Service Package

Автономный бот для управления дельтой портфеля опционов.

Режимы работы:
- NEUTRAL: Дельта = 0, микро-хеджирование фьючерсами (H1 внутри уровней)
- DIRECTIONAL: Дельта смещена в сторону тренда (H1 пробой)
- DEFENSIVE: Покупка защитных опционов (H4 пробой)

Usage:
    from bybit_options.services.hedger import DeltaHedgerBot, HedgerConfig, HedgerMode
    
    config = HedgerConfig(
        mode=HedgerMode.NEUTRAL,
        threshold=0.003,
        enabled=True
    )
    
    bot = DeltaHedgerBot(connector, db_pool, config)
    await bot.start()
"""

from .models import (
    HedgerMode,
    HedgerConfig,
    FractalSignal,
    OrderResult,
    HedgeAction,
)

from .config import (
    HedgerConfigLoader,
    get_default_config,
)

from .position_monitor import PositionMonitor

from .order_executor import (
    OrderExecutor,
    APIError,
    RateLimitError,
)

from .bot import DeltaHedgerBot
from .option_solver import OptionSolver


__all__ = [
    "DeltaHedgerBot",
    # Models
    "HedgerMode",
    "HedgerConfig",
    "FractalSignal",
    "OrderResult",
    "HedgeAction",
    # Config
    "HedgerConfigLoader",
    "get_default_config",
    # Components
    "PositionMonitor",
    "OrderExecutor",
    "OptionSolver",
    # Exceptions
    "RateLimitError",
    "APIError",
]

"""
Delta Hedger Bot - Position Monitor

Мониторинг текущей дельты портфеля (опционы + фьючерсы).
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class ConnectorProtocol(Protocol):
    """
    Протокол для connector (для type hints и тестирования).
    
    Определяет минимальный интерфейс, необходимый для PositionMonitor.
    """
    
    async def get_positions(
        self, 
        category: str, 
        symbol: Optional[str] = None,
        settle_coin: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch positions from exchange."""
        ...


class PositionFetchError(Exception):
    """Failed to fetch positions from exchange."""
    pass


class PositionMonitor:
    """
    Мониторинг текущей дельты портфеля.
    ...
    """
    
    def __init__(
        self, 
        connector: ConnectorProtocol,
        base_coin: str = "BTC"
    ):
        """
        Инициализирует PositionMonitor.
        
        Args:
            connector: Bybit connector instance
            base_coin: Базовая монета (BTC или ETH)
        """
        self.connector = connector
        self.base_coin = base_coin
        self._last_options_delta: Optional[float] = None
        self._last_futures_delta: Optional[float] = None
        self._last_total_delta: Optional[float] = None
    
    async def get_portfolio_delta(self) -> float:
        """
        Возвращает общую дельту портфеля в BTC/ETH.
        
        Returns:
            Total delta как float (положительный = long exposure,
            отрицательный = short exposure)
            
        Raises:
            PositionFetchError: Если не удалось получить данные с биржи
        """
        options_delta = await self._get_options_delta()
        futures_delta = await self._get_futures_delta()
        
        total_delta = options_delta + futures_delta
        
        # Cache for debugging
        self._last_options_delta = options_delta
        self._last_futures_delta = futures_delta
        self._last_total_delta = total_delta
        
        logger.debug(
            "Portfolio delta calculated",
            extra={
                "options_delta": options_delta,
                "futures_delta": futures_delta,
                "total_delta": total_delta,
                "base_coin": self.base_coin
            }
        )
        
        return total_delta
    
    async def _get_options_delta(self) -> float:
        """
        Получает суммарную дельту опционных позиций.
        
        Returns:
            Сумма (delta × size) для всех опционов
            
        Raises:
            PositionFetchError: Если запрос упал
        """
        try:
            positions = await self.connector.get_positions(
                category="option",
                settle_coin=self.base_coin
            )
        except Exception as e:
            logger.error(f"Failed to fetch options positions: {e}")
            raise PositionFetchError(f"Options fetch failed: {e}") from e
        
        total_delta = 0.0
        
        for pos in positions:
            try:
                # Parse position data
                size = float(pos.get("size", 0))
                if size == 0:
                    continue
                
                # Delta from Bybit API (may be returned as 'delta' or 'positionDelta')
                delta_raw = pos.get("delta") or pos.get("positionDelta") or 0
                delta = float(delta_raw)
                
                # Side (для логирования)
                side = pos.get("side", "")
                symbol = pos.get("symbol", "")
                
                # Bybit возвращает delta * size уже учтённую,
                # но мы перепроверяем направление
                # Для SHORT позиции size < 0, тогда delta уже инвертирована
                position_delta = delta * size
                
                total_delta += position_delta
                
                logger.debug(
                    f"Option position: {symbol} size={size} delta={delta} "
                    f"position_delta={position_delta}"
                )
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse option position: {pos}, error: {e}")
                continue
        
        return total_delta
    
    async def _get_futures_delta(self) -> float:
        """
        Получает суммарную дельту фьючерсных позиций.
        
        Returns:
            Сумма position sizes с учётом направления
            
        Raises:
            PositionFetchError: Если запрос упал
        """
        # Определяем символ для base_coin
        symbol = f"{self.base_coin}USDT"
        
        try:
            positions = await self.connector.get_positions(
                category="linear",
                symbol=symbol
            )
        except Exception as e:
            logger.error(f"Failed to fetch futures positions: {e}")
            raise PositionFetchError(f"Futures fetch failed: {e}") from e
        
        total_delta = 0.0
        
        for pos in positions:
            try:
                size = float(pos.get("size", 0))
                if size == 0:
                    continue
                
                side = pos.get("side", "").lower()
                symbol = pos.get("symbol", "")
                
                # LONG (Buy): positive delta
                # SHORT (Sell): negative delta
                if side == "buy":
                    position_delta = size
                elif side == "sell":
                    position_delta = -size
                else:
                    logger.warning(f"Unknown side: {side} for {symbol}")
                    continue
                
                total_delta += position_delta
                
                logger.debug(
                    f"Futures position: {symbol} side={side} size={size} "
                    f"position_delta={position_delta}"
                )
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse futures position: {pos}, error: {e}")
                continue
        
        return total_delta
    
    async def get_detailed_delta(self) -> Dict[str, Any]:
        """
        Возвращает детальную информацию о дельте.
        
        Returns:
            Dict с options_delta, futures_delta, total_delta и позициями
        """
        options_delta = await self._get_options_delta()
        futures_delta = await self._get_futures_delta()
        total_delta = options_delta + futures_delta
        
        return {
            "options_delta": options_delta,
            "futures_delta": futures_delta,
            "total_delta": total_delta,
            "base_coin": self.base_coin,
            "is_net_long": total_delta > 0,
            "is_net_short": total_delta < 0,
            "is_neutral": abs(total_delta) < 0.001,  # < 0.001 BTC считаем нейтральным
        }
    
    @property
    def last_delta(self) -> Optional[float]:
        """Последняя рассчитанная дельта (cached)."""
        return self._last_total_delta
    
    @property
    def last_options_delta(self) -> Optional[float]:
        """Последняя дельта опционов (cached)."""
        return self._last_options_delta
    
    @property
    def last_futures_delta(self) -> Optional[float]:
        """Последняя дельта фьючерсов (cached)."""
        return self._last_futures_delta

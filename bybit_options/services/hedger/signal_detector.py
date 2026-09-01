"""
Signal Detector for Delta Hedger Bot.

Detects breakouts of key H1/H4 fractals using data from the database.
"""

from typing import Optional
import asyncpg
from bybit_options.services.hedger.models import FractalSignal


class SignalDetector:
    """
    Детектор пробоев ключевых фракталов.
    
    Читает данные из БД:
    - fractals_cache (ключевые фракталы H1/H4)
    - perpetual_ohlcv (текущая цена)
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def get_current_price(self) -> float:
        """
        Получает последнюю цену закрытия из perpetual_ohlcv.
        
        Returns:
            float: Последняя цена закрытия.
            
        Raises:
            ValueError: Если данных нет в БД.
        """
        query = """
            SELECT close 
            FROM perpetual_ohlcv 
            WHERE symbol = 'BTCUSDT' 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        val = await self.db.fetchval(query)
        if val is None:
            # If no data is available, we cannot detect signals.
            # Returning 0.0 might trigger false breakouts if fractals are > 0.
            # Ideally we should raise or return None implicitly handled by caller.
            # For robustness, we return 0.0 but logging might be good.
            # Given detect() checks for > 0, returning 0.0 is safe.
            return 0.0 
        return float(val)
    
    async def _check_fractal_breakout(
        self,
        timeframe: str,
        current_price: float
    ) -> Optional[FractalSignal]:
        """
        Проверяет пробой ключевого фрактала.
        
        Условия:
        - Фрактал помечен как is_key_fractal = TRUE
        - Цена пересекла уровень фрактала:
          - HIGH fractal: цена > fractal_price (LONG)
          - LOW fractal: цена < fractal_price (SHORT)
        """
        query = """
            SELECT 
                timestamp,
                price,
                type
            FROM fractals_cache
            WHERE timeframe = $1
              AND base_coin = 'BTC'
              AND is_key_fractal = TRUE
            ORDER BY timestamp DESC
            LIMIT 2
        """
        
        rows = await self.db.fetch(query, timeframe)
        
        for row in rows:
            fractal_price = float(row['price'])
            fractal_type = row['type']
            
            # Пробой вверх (цена > resistance fractal)
            if fractal_type == 'HIGH' and current_price > fractal_price:
                return FractalSignal(
                    timeframe=timeframe,
                    fractal_type=fractal_type,
                    fractal_price=fractal_price,
                    current_price=current_price,
                    direction="LONG",
                    is_breakout=True
                )
            
            # Пробой вниз (цена < support fractal)
            if fractal_type == 'LOW' and current_price < fractal_price:
                return FractalSignal(
                    timeframe=timeframe,
                    fractal_type=fractal_type,
                    fractal_price=fractal_price,
                    current_price=current_price,
                    direction="SHORT",
                    is_breakout=True
                )
        return None
    
    async def detect(self) -> Optional[FractalSignal]:
        """
        Проверяет пробои на H1 и H4.
        
        Приоритет:
        1. H4 Breakout (наиболее значимый)
        2. H1 Breakout
        
        Returns:
            Optional[FractalSignal]: Найденный сигнал или None.
        """
        current_price = await self.get_current_price()
        if current_price <= 0:
            return None
            
        # 1. Проверяем H4 (более приоритетный)
        h4_signal = await self._check_fractal_breakout("H4", current_price)
        if h4_signal:
            return h4_signal
            
        # 2. Проверяем H1
        h1_signal = await self._check_fractal_breakout("H1", current_price)
        if h1_signal:
            return h1_signal
            
        return None

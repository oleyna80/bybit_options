# 🎯 Задача: DELTA-001 — REST-based LargeTradeCollector

**Статус:** 🟡 READY FOR EXECUTION  
**Приоритет:** HIGH  
**Оценка времени:** 2-3 часа  
**Исполнитель:** Backend Developer  
**Зависит от:** DELTA-004 (TimescaleDB Migration) — должна быть выполнена

---

## 📋 Контекст

Мы внедряем систему **Delta Volume Analytics** для сбора и анализа объёмной дельты крупных сделок (whale trades). Это позволит улучшить точность сигналов опционной стратегии.

**Полное ТЗ проекта:** [delta_volume_analytics.tz.md](delta_volume_analytics.tz.md)

**Текущая задача:** Создать collector для сбора крупных сделок через REST API (polling каждые 10 секунд).

---

## 🎯 Цель

Создать `LargeTradeCollector` — сервис для сбора крупных сделок (>= 5 BTC, >= 50 ETH) с Bybit через REST API и сохранения в TimescaleDB.

**Ключевые характеристики:**
- REST polling каждые 10 секунд (НЕ WebSocket)
- Фильтрация по конфигурируемым порогам
- Deduplication по `trade_id`
- Graceful shutdown

---

## ✅ Acceptance Criteria

- [ ] AC1: Создана директория `bybit_options/services/delta/collectors/`
- [ ] AC2: Создан `base_collector.py` с абстрактным классом `BaseCollector`
- [ ] AC3: Создан `large_trade_collector.py` с классом `LargeTradeCollector`
- [ ] AC4: Collector использует Bybit REST API `/v5/market/recent-trade`
- [ ] AC5: Polling интервал 10 секунд (конфигурируемый)
- [ ] AC6: Фильтрация: BTC >= 5, ETH >= 50 (пороги из `delta_config` таблицы)
- [ ] AC7: Deduplication по `trade_id` (ON CONFLICT DO NOTHING в SQL)
- [ ] AC8: Graceful shutdown по SIGTERM/SIGINT
- [ ] AC9: Логирование: trades/min статистика
- [ ] AC10: CLI скрипт `scripts/run_delta_collector.py --trades`
- [ ] AC11: Тест `tests/test_delta/test_large_trade_collector.py` проходит

---

## 📁 Файлы

### Создать:

```
bybit_options/services/delta/collectors/__init__.py
bybit_options/services/delta/collectors/base_collector.py
bybit_options/services/delta/collectors/large_trade_collector.py
scripts/run_delta_collector.py
tests/test_delta/__init__.py
tests/test_delta/test_large_trade_collector.py
```

### Существующие (использовать):

```
bybit_options/services/bybit_connector.py    # BybitConnector для API calls
bybit_options/models/delta_models.py         # LargeTradeModel
bybit_options/services/delta/storage_service.py  # StorageService.save_large_trades()
bybit_options/services/delta/database_config.py  # db connection
```

---

## 🏗️ Архитектура

### Схема

```
┌─────────────────────────────────────────────────────────────┐
│                    LargeTradeCollector                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │BybitConnector│───►│ LargeTradeCollector│───►│StorageService│
│  │/v5/market/   │    │ - filter by qty  │    │save_large_ │  │
│  │recent-trade  │    │ - dedup by id    │    │trades()    │  │
│  └─────────────┘    └──────────────────┘    └───────────┘  │
│                              │                              │
│                              ▼                              │
│                     ┌───────────────┐                       │
│                     │  TimescaleDB  │                       │
│                     │ large_trades  │                       │
│                     └───────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Every 10 seconds:
   ├── GET /v5/market/recent-trade?symbol=BTCUSDT&limit=500
   ├── GET /v5/market/recent-trade?symbol=ETHUSDT&limit=500
   │
2. Filter trades:
   ├── BTCUSDT: quantity >= 5.0
   ├── ETHUSDT: quantity >= 50.0
   │
3. Convert to LargeTradeModel
   │
4. Save to DB (ON CONFLICT DO NOTHING)
   │
5. Log stats
```

---

## 📝 Спецификации классов

### BaseCollector (abstract)

```python
# bybit_options/services/delta/collectors/base_collector.py

from abc import ABC, abstractmethod
import asyncio
import signal
from loguru import logger

class BaseCollector(ABC):
    """Abstract base class for data collectors"""
    
    def __init__(self, interval_seconds: int = 10):
        self.interval_seconds = interval_seconds
        self.running = False
        self.stats = {
            'iterations': 0,
            'items_collected': 0,
            'items_saved': 0,
            'errors': 0,
            'start_time': None
        }
    
    @abstractmethod
    async def collect_once(self) -> int:
        """Execute one collection cycle. Returns number of items saved."""
        pass
    
    async def run(self) -> None:
        """Start infinite collection loop with graceful shutdown"""
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        
        logger.info(f"🚀 Starting {self.__class__.__name__}")
        
        while self.running:
            try:
                self.stats['iterations'] += 1
                saved = await self.collect_once()
                self.stats['items_saved'] += saved
                
                # Log stats every 10 iterations
                if self.stats['iterations'] % 10 == 0:
                    self._log_stats()
                
                await asyncio.sleep(self.interval_seconds)
                
            except asyncio.CancelledError:
                logger.info(f"⏹️ {self.__class__.__name__} cancelled")
                break
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ Error in {self.__class__.__name__}: {e}")
                await asyncio.sleep(self.interval_seconds)
        
        logger.info(f"🛑 {self.__class__.__name__} stopped")
    
    async def stop(self) -> None:
        """Stop the collector gracefully"""
        logger.info(f"⏹️ Stopping {self.__class__.__name__}...")
        self.running = False
    
    def _log_stats(self) -> None:
        """Log collection statistics"""
        elapsed = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        rate = self.stats['items_saved'] / elapsed * 60 if elapsed > 0 else 0
        logger.info(
            f"📊 {self.__class__.__name__} stats: "
            f"iterations={self.stats['iterations']}, "
            f"saved={self.stats['items_saved']}, "
            f"errors={self.stats['errors']}, "
            f"rate={rate:.1f}/min"
        )
```

### LargeTradeCollector

```python
# bybit_options/services/delta/collectors/large_trade_collector.py

from decimal import Decimal
from typing import List, Dict
from datetime import datetime, timezone
from loguru import logger

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.storage_service import StorageService
from bybit_options.services.delta.database_config import db
from bybit_options.models.delta_models import LargeTradeModel
from .base_collector import BaseCollector


class LargeTradeCollector(BaseCollector):
    """
    Collector for large trades (whale trades) from Bybit REST API.
    
    Features:
    - Polls /v5/market/recent-trade every N seconds
    - Filters trades by configurable thresholds
    - Saves to TimescaleDB with deduplication
    
    Configuration:
    - Thresholds loaded from delta_config table
    - Default: BTCUSDT >= 5 BTC, ETHUSDT >= 50 ETH
    """
    
    DEFAULT_THRESHOLDS = {
        'BTCUSDT': Decimal('5.0'),
        'ETHUSDT': Decimal('50.0'),
    }
    
    def __init__(
        self,
        connector: BybitConnector,
        storage: StorageService,
        symbols: List[str] = None,
        interval_seconds: int = 10,
        category: str = 'linear'  # linear = perpetual futures
    ):
        super().__init__(interval_seconds=interval_seconds)
        self.connector = connector
        self.storage = storage
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT']
        self.category = category
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        self._last_trade_ids: Dict[str, set] = {s: set() for s in self.symbols}
    
    async def load_thresholds_from_db(self) -> None:
        """Load thresholds from delta_config table"""
        try:
            async with db.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT symbol, threshold_qty FROM delta_config WHERE active = true"
                )
                for row in rows:
                    self.thresholds[row['symbol']] = Decimal(str(row['threshold_qty']))
                logger.info(f"📋 Loaded thresholds: {self.thresholds}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load thresholds from DB, using defaults: {e}")
    
    async def collect_once(self) -> int:
        """
        Execute one collection cycle.
        
        Returns: Number of new trades saved to DB
        """
        all_trades: List[LargeTradeModel] = []
        
        for symbol in self.symbols:
            try:
                # Fetch recent trades from Bybit
                raw_trades = await self.connector.get_recent_trades(
                    symbol=symbol,
                    category=self.category,
                    limit=500
                )
                
                if not raw_trades:
                    continue
                
                # Get threshold for this symbol
                threshold = self.thresholds.get(symbol, Decimal('5.0'))
                
                # Filter and convert
                for trade in raw_trades:
                    trade_id = trade.get('execId') or trade.get('id')
                    quantity = Decimal(str(trade.get('size') or trade.get('qty', 0)))
                    
                    # Skip if below threshold
                    if quantity < threshold:
                        continue
                    
                    # Skip if already seen (dedup within session)
                    if trade_id in self._last_trade_ids[symbol]:
                        continue
                    
                    # Parse trade
                    model = LargeTradeModel(
                        exchange='bybit',
                        market_type='perpetual',
                        symbol=symbol,
                        trade_id=trade_id,
                        price=Decimal(str(trade.get('price', 0))),
                        quantity=quantity,
                        side=trade.get('side', 'Buy'),
                        timestamp=datetime.fromtimestamp(
                            int(trade.get('time', 0)) / 1000,
                            tz=timezone.utc
                        )
                    )
                    all_trades.append(model)
                    
                    # Track seen IDs (keep last 1000)
                    self._last_trade_ids[symbol].add(trade_id)
                    if len(self._last_trade_ids[symbol]) > 1000:
                        self._last_trade_ids[symbol] = set(
                            list(self._last_trade_ids[symbol])[-500:]
                        )
                        
            except Exception as e:
                logger.error(f"❌ Error fetching {symbol}: {e}")
                self.stats['errors'] += 1
        
        # Save to DB
        if all_trades:
            saved = await self.storage.save_large_trades(all_trades)
            self.stats['items_collected'] += len(all_trades)
            
            if saved > 0:
                logger.info(
                    f"🐋 Collected {len(all_trades)} whale trades, "
                    f"saved {saved} new"
                )
            
            return saved
        
        return 0
```

### CLI Script

```python
# scripts/run_delta_collector.py

#!/usr/bin/env python3
"""
Delta Collector CLI
Usage:
    python scripts/run_delta_collector.py --trades
    python scripts/run_delta_collector.py --trades --symbols BTCUSDT,ETHUSDT
    python scripts/run_delta_collector.py --trades --interval 15
"""

import asyncio
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from dotenv import load_dotenv

load_dotenv()


async def run_trade_collector(symbols: list, interval: int):
    """Run LargeTradeCollector"""
    from bybit_options.services.bybit_connector import BybitConnector
    from bybit_options.services.delta.storage_service import StorageService
    from bybit_options.services.delta.database_config import db
    from bybit_options.services.delta.collectors import LargeTradeCollector
    
    # Initialize
    await db.connect()
    connector = BybitConnector()
    await connector.connect()
    storage = StorageService()
    
    collector = LargeTradeCollector(
        connector=connector,
        storage=storage,
        symbols=symbols,
        interval_seconds=interval
    )
    
    # Load thresholds from DB
    await collector.load_thresholds_from_db()
    
    try:
        await collector.run()
    finally:
        await connector.close()
        await db.close()


def main():
    parser = argparse.ArgumentParser(description='Delta Collector CLI')
    parser.add_argument('--trades', action='store_true', help='Run LargeTradeCollector')
    parser.add_argument('--orderbook', action='store_true', help='Run OrderbookCollector')
    parser.add_argument('--oi', action='store_true', help='Run OpenInterestCollector')
    parser.add_argument('--symbols', type=str, default='BTCUSDT,ETHUSDT',
                        help='Comma-separated symbols')
    parser.add_argument('--interval', type=int, default=10,
                        help='Polling interval in seconds')
    
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    if args.trades:
        logger.info(f"🚀 Starting LargeTradeCollector for {symbols}")
        asyncio.run(run_trade_collector(symbols, args.interval))
    elif args.orderbook:
        logger.info("OrderbookCollector not implemented yet")
    elif args.oi:
        logger.info("OpenInterestCollector not implemented yet")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
```

---

## 🔌 Bybit API Reference

### Endpoint: /v5/market/recent-trade

```
GET https://api.bybit.com/v5/market/recent-trade

Parameters:
- category: spot | linear | inverse | option
- symbol: BTCUSDT, ETHUSDT, etc.
- limit: 1-1000 (default 500)

Response:
{
  "result": {
    "list": [
      {
        "execId": "2100000000007704627",
        "symbol": "BTCUSDT",
        "price": "93000.00",
        "size": "5.123",
        "side": "Buy",
        "time": "1705702800000",
        "isBlockTrade": false
      }
    ]
  }
}
```

---

## 🧪 Testing

### Unit Test

```python
# tests/test_delta/test_large_trade_collector.py

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from bybit_options.services.delta.collectors.large_trade_collector import LargeTradeCollector


class TestLargeTradeCollector:
    
    @pytest.fixture
    def mock_connector(self):
        connector = AsyncMock()
        connector.get_recent_trades.return_value = [
            {
                'execId': 'trade1',
                'symbol': 'BTCUSDT',
                'price': '93000.00',
                'size': '6.5',  # Above threshold
                'side': 'Buy',
                'time': '1705702800000'
            },
            {
                'execId': 'trade2',
                'symbol': 'BTCUSDT',
                'price': '93000.00',
                'size': '0.5',  # Below threshold
                'side': 'Sell',
                'time': '1705702801000'
            }
        ]
        return connector
    
    @pytest.fixture
    def mock_storage(self):
        storage = AsyncMock()
        storage.save_large_trades.return_value = 1
        return storage
    
    @pytest.mark.asyncio
    async def test_filter_by_threshold(self, mock_connector, mock_storage):
        """Should only collect trades >= threshold"""
        collector = LargeTradeCollector(
            connector=mock_connector,
            storage=mock_storage,
            symbols=['BTCUSDT'],
            interval_seconds=10
        )
        
        saved = await collector.collect_once()
        
        # Only 1 trade should pass (6.5 >= 5.0)
        assert mock_storage.save_large_trades.called
        trades = mock_storage.save_large_trades.call_args[0][0]
        assert len(trades) == 1
        assert trades[0].quantity == Decimal('6.5')
    
    @pytest.mark.asyncio
    async def test_deduplication(self, mock_connector, mock_storage):
        """Should skip duplicate trade_ids"""
        collector = LargeTradeCollector(
            connector=mock_connector,
            storage=mock_storage,
            symbols=['BTCUSDT']
        )
        
        # First call
        await collector.collect_once()
        
        # Second call with same data
        await collector.collect_once()
        
        # Second call should return 0 (all duplicates)
        # Verify only 1 call saved trades
        assert mock_storage.save_large_trades.call_count == 1
```

### Manual Test

```bash
# Activate venv
source .venv/bin/activate

# Run collector for 30 seconds
timeout 30 python scripts/run_delta_collector.py --trades --interval 10

# Check database
PGPASSWORD=<SET_IN_LOCAL_ENV> psql -h localhost -U trading_user -d trading_platform -c \
  "SELECT COUNT(*) FROM large_trades;"

PGPASSWORD=<SET_IN_LOCAL_ENV> psql -h localhost -U trading_user -d trading_platform -c \
  "SELECT * FROM large_trades ORDER BY timestamp DESC LIMIT 5;"
```

---

## ⚠️ Важно

1. **Используй существующий BybitConnector** — не создавай новый
2. **Используй существующий StorageService** — метод `save_large_trades()` уже есть
3. **Проверь что DELTA-004 выполнена** — таблица `large_trades` должна существовать
4. **НЕ используй WebSocket** — только REST polling
5. **Thresholds из БД** — загружай из `delta_config` таблицы

---

## 📋 Checklist перед сдачей

- [ ] Директория `collectors/` создана
- [ ] `BaseCollector` реализован
- [ ] `LargeTradeCollector` реализован
- [ ] CLI скрипт работает: `python scripts/run_delta_collector.py --trades`
- [ ] Collector собирает данные и сохраняет в БД
- [ ] Graceful shutdown работает (CTRL+C)
- [ ] Unit test проходит
- [ ] Логирование статистики каждые ~2 минуты

---

## 🚀 Следующий шаг

После выполнения → **DELTA-002** (OrderbookCollector) или **DELTA-003** (OpenInterestCollector)

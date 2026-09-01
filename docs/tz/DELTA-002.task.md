# 🎯 Задача: DELTA-002 — REST-based OrderbookCollector

**Статус:** 🟡 READY FOR EXECUTION  
**Приоритет:** HIGH  
**Оценка времени:** 2 часа  
**Исполнитель:** Backend Developer  
**Зависит от:** DELTA-001 (LargeTradeCollector) — должна быть выполнена ✅

---

## 📋 Контекст

Мы внедряем систему **Delta Volume Analytics** для сбора и анализа объёмной дельты. Первый collector (DELTA-001) уже реализован и работает.

**Полное ТЗ проекта:** [delta_volume_analytics.tz.md](delta_volume_analytics.tz.md)  
**Предыдущая задача:** [DELTA-001.task.md](DELTA-001.task.md) ✅

**Текущая задача:** Создать collector для сбора orderbook snapshots через REST API (polling каждые 5 секунд).

---

## 🎯 Цель

Создать `OrderbookCollector` — сервис для сбора снимков orderbook (top 20 levels) с Bybit через REST API и сохранения в TimescaleDB с расчётом imbalance.

**Ключевые характеристики:**
- REST polling каждые 5 секунд (НЕ WebSocket)
- Top 20 bid/ask levels
- Расчёт imbalance: `(total_bid_qty - total_ask_qty) / (total_bid_qty + total_ask_qty)`
- Хранение levels в JSONB

---

## ✅ Acceptance Criteria

- [ ] AC1: Создан файл `orderbook_collector.py` в директории `collectors/`
- [ ] AC2: Класс `OrderbookCollector` наследует `BaseCollector`
- [ ] AC3: Collector использует Bybit REST API `/v5/market/orderbook`
- [ ] AC4: Polling интервал 5 секунд (конфигурируемый)
- [ ] AC5: Собирает top 20 levels (bids + asks)
- [ ] AC6: Расчёт imbalance по формуле `(bid_vol - ask_vol) / (bid_vol + ask_vol)`
- [ ] AC7: Сохранение в таблицу `orderbook_snapshots` (уже существует)
- [ ] AC8: CLI опция `--orderbook` в `run_delta_collector.py`
- [ ] AC9: Тест проходит
- [ ] AC10: Можно запустить одновременно с `--trades` и `--orderbook`

---

## 📁 Файлы

### Создать:

```
bybit_options/services/delta/collectors/orderbook_collector.py
tests/test_delta/test_orderbook_collector.py
```

### Изменить:

```
bybit_options/services/delta/collectors/__init__.py  # Добавить экспорт
scripts/run_delta_collector.py                        # Добавить --orderbook логику
```

### Существующие (использовать):

```
bybit_options/services/delta/collectors/base_collector.py   # Наследоваться
bybit_options/services/bybit_connector.py                   # BybitConnector
bybit_options/models/delta_models.py                        # OrderbookSnapshotModel
bybit_options/services/delta/storage_service.py             # StorageService
bybit_options/services/delta/database_config.py             # db connection
```

---

## 🏗️ Архитектура

### Схема

```
┌─────────────────────────────────────────────────────────────┐
│                    OrderbookCollector                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │BybitConnector│───►│ OrderbookCollector│───►│StorageService│
│  │/v5/market/   │    │ - top 20 levels  │    │save_orderbook│
│  │orderbook     │    │ - calc imbalance │    │_snapshots()  │
│  └─────────────┘    └──────────────────┘    └───────────┘  │
│                              │                              │
│                              ▼                              │
│                     ┌───────────────┐                       │
│                     │  TimescaleDB  │                       │
│                     │orderbook_     │                       │
│                     │ snapshots     │                       │
│                     └───────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Every 5 seconds:
   ├── GET /v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=20
   ├── GET /v5/market/orderbook?category=linear&symbol=ETHUSDT&limit=20
   │
2. Parse response:
   ├── Extract bids: [[price, qty], ...]
   ├── Extract asks: [[price, qty], ...]
   │
3. Calculate imbalance:
   │   bid_volume = sum(qty for price, qty in bids)
   │   ask_volume = sum(qty for price, qty in asks)
   │   imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
   │
4. Create OrderbookSnapshotModel
   │
5. Save to TimescaleDB
   │
6. Log stats
```

---

## 🔌 Bybit API Reference

### Endpoint: /v5/market/orderbook

```
GET https://api.bybit.com/v5/market/orderbook

Parameters:
- category: spot | linear | inverse | option
- symbol: BTCUSDT, ETHUSDT, etc.
- limit: 1, 25, 50, 100, 200, 500 (default 25)

Response:
{
  "retCode": 0,
  "result": {
    "s": "BTCUSDT",
    "b": [                          // bids (price descending)
      ["93000.00", "5.123"],        // [price, qty]
      ["92999.50", "2.500"],
      ...
    ],
    "a": [                          // asks (price ascending)
      ["93000.50", "3.200"],
      ["93001.00", "1.800"],
      ...
    ],
    "ts": 1705702800000,           // timestamp
    "u": 123456789                  // update ID
  }
}
```

**Важно:** Для perpetual futures используй `limit=20` (ближайший к 20 — это 25).

---

## 📝 Спецификации классов

### OrderbookCollector

```python
# bybit_options/services/delta/collectors/orderbook_collector.py

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from loguru import logger

from bybit_options.models.delta_models import OrderbookSnapshotModel, OrderbookLevel
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.database_config import db
from bybit_options.services.delta.storage_service import StorageService

from .base_collector import BaseCollector


class OrderbookCollector(BaseCollector):
    """
    Collector for orderbook snapshots from Bybit REST API.
    
    Features:
    - Polls /v5/market/orderbook every N seconds (default 5)
    - Collects top 20 bid/ask levels
    - Calculates order book imbalance
    - Saves to TimescaleDB
    
    Imbalance formula:
        imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol)
        Range: -1.0 (all asks) to +1.0 (all bids)
        Positive = buying pressure, Negative = selling pressure
    """

    def __init__(
        self,
        connector: BybitConnector,
        storage: StorageService,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 5,
        depth: int = 20,
        category: str = "linear",
    ) -> None:
        super().__init__(interval_seconds=interval_seconds)
        self.connector = connector
        self.storage = storage
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT"]
        self.depth = depth
        self.category = category

    async def collect_once(self) -> int:
        """
        Execute one collection cycle.
        
        Returns: Number of snapshots saved to DB
        """
        snapshots: List[OrderbookSnapshotModel] = []

        for symbol in self.symbols:
            try:
                data = await self._fetch_orderbook(symbol)
                if not data:
                    continue

                snapshot = self._parse_orderbook(symbol, data)
                if snapshot:
                    snapshots.append(snapshot)

            except Exception as exc:
                self.stats["errors"] += 1
                logger.error(f"❌ Error fetching orderbook {symbol}: {exc}")

        if not snapshots:
            return 0

        self.stats["items_collected"] += len(snapshots)
        saved = await self.storage.save_orderbook_snapshots(snapshots)

        if saved > 0:
            # Log imbalance for each symbol
            for snap in snapshots:
                imb_pct = snap.imbalance * 100
                direction = "📈 BID" if snap.imbalance > 0 else "📉 ASK"
                logger.debug(
                    f"📊 {snap.symbol} orderbook: {direction} pressure {abs(imb_pct):.1f}%"
                )

        return saved

    async def _fetch_orderbook(self, symbol: str) -> dict | None:
        """Fetch orderbook from Bybit API."""
        # Use existing connector method or add new one
        params = {
            "category": self.category,
            "symbol": symbol,
            "limit": 25,  # Closest to 20 that API supports
        }

        data = await self.connector._public_request("/v5/market/orderbook", params)

        if data.get("retCode") != 0:
            logger.error(
                f"Orderbook fetch failed for {symbol}: "
                f"[{data.get('retCode')}] {data.get('retMsg')}"
            )
            return None

        return data.get("result", {})

    def _parse_orderbook(self, symbol: str, data: dict) -> OrderbookSnapshotModel | None:
        """Parse raw orderbook data into model."""
        try:
            raw_bids = data.get("b", [])[:self.depth]
            raw_asks = data.get("a", [])[:self.depth]

            bids = [
                OrderbookLevel(price=Decimal(p), quantity=Decimal(q))
                for p, q in raw_bids
            ]
            asks = [
                OrderbookLevel(price=Decimal(p), quantity=Decimal(q))
                for p, q in raw_asks
            ]

            # Calculate imbalance
            bid_volume = sum(level.quantity for level in bids)
            ask_volume = sum(level.quantity for level in asks)
            total_volume = bid_volume + ask_volume

            imbalance = Decimal("0")
            if total_volume > 0:
                imbalance = (bid_volume - ask_volume) / total_volume

            timestamp_ms = data.get("ts")
            timestamp = (
                datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc)
                if timestamp_ms
                else datetime.now(timezone.utc)
            )

            return OrderbookSnapshotModel(
                exchange="bybit",
                market_type="perpetual",
                symbol=symbol,
                bids=bids,
                asks=asks,
                imbalance=float(imbalance),
                timestamp=timestamp,
            )

        except Exception as exc:
            logger.error(f"Failed to parse orderbook for {symbol}: {exc}")
            return None
```

---

## 📦 Модель данных

### OrderbookSnapshotModel (уже существует)

```python
# bybit_options/models/delta_models.py

class OrderbookLevel(BaseModel):
    price: Decimal
    quantity: Decimal

class OrderbookSnapshotModel(BaseModel):
    exchange: str = 'bybit'
    market_type: str = 'perpetual'
    symbol: str
    bids: List[OrderbookLevel] = Field(max_items=20)
    asks: List[OrderbookLevel] = Field(max_items=20)
    imbalance: float = Field(ge=-1.0, le=1.0)
    timestamp: datetime
```

### Таблица (уже существует)

```sql
-- database_migrations/008_create_delta_hypertables.sql

CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange TEXT NOT NULL DEFAULT 'bybit',
    market_type TEXT NOT NULL DEFAULT 'perpetual',
    symbol TEXT NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    imbalance NUMERIC(5,4) NOT NULL,
    UNIQUE (timestamp, exchange, symbol)
);
```

---

## 🔧 Изменения в существующих файлах

### 1. collectors/__init__.py

```python
# bybit_options/services/delta/collectors/__init__.py

"""Delta collectors package."""

from .base_collector import BaseCollector
from .large_trade_collector import LargeTradeCollector
from .orderbook_collector import OrderbookCollector  # NEW

__all__ = [
    "BaseCollector",
    "LargeTradeCollector",
    "OrderbookCollector",  # NEW
]
```

### 2. run_delta_collector.py

Добавить функцию `run_orderbook_collector` и логику для `--orderbook`:

```python
# scripts/run_delta_collector.py

# ... existing imports ...
from bybit_options.services.delta.collectors import LargeTradeCollector, OrderbookCollector


async def run_orderbook_collector(symbols: List[str], interval: int) -> None:
    """Run OrderbookCollector loop."""
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")

    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

    connector = None
    try:
        await db.connect()

        connector = BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
        )
        await connector.connect()

        storage = StorageService()
        collector = OrderbookCollector(
            connector=connector,
            storage=storage,
            symbols=symbols,
            interval_seconds=interval,
        )

        await collector.run()
    finally:
        if connector is not None:
            await connector.close()
        await db.close()


def main() -> None:
    # ... existing arg parsing ...

    if args.trades:
        logger.info(f"🚀 Starting LargeTradeCollector for {symbols}")
        asyncio.run(run_trade_collector(symbols, args.interval))
    elif args.orderbook:  # NEW
        logger.info(f"📊 Starting OrderbookCollector for {symbols}")
        asyncio.run(run_orderbook_collector(symbols, args.interval))
    else:
        parser.print_help()
```

---

## 🧪 Testing

### Unit Test

```python
# tests/test_delta/test_orderbook_collector.py

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from bybit_options.services.delta.collectors.orderbook_collector import (
    OrderbookCollector,
)


@pytest.fixture
def mock_connector():
    connector = AsyncMock()
    return connector


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.save_orderbook_snapshots.return_value = 1
    return storage


@pytest.fixture
def sample_orderbook_response():
    return {
        "retCode": 0,
        "result": {
            "s": "BTCUSDT",
            "b": [
                ["93000.00", "5.000"],
                ["92999.50", "3.000"],
                ["92999.00", "2.000"],
            ],
            "a": [
                ["93000.50", "4.000"],
                ["93001.00", "2.000"],
                ["93001.50", "1.000"],
            ],
            "ts": 1705702800000,
            "u": 123456789,
        },
    }


@pytest.mark.asyncio
async def test_imbalance_calculation(mock_connector, mock_storage, sample_orderbook_response):
    """
    Test imbalance calculation:
    bid_volume = 5 + 3 + 2 = 10
    ask_volume = 4 + 2 + 1 = 7
    imbalance = (10 - 7) / (10 + 7) = 3/17 ≈ 0.176
    """
    mock_connector._public_request = AsyncMock(return_value=sample_orderbook_response)

    collector = OrderbookCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
        interval_seconds=5,
    )

    saved = await collector.collect_once()

    assert saved == 1
    assert mock_storage.save_orderbook_snapshots.called
    snapshots = mock_storage.save_orderbook_snapshots.call_args[0][0]
    assert len(snapshots) == 1

    snapshot = snapshots[0]
    assert snapshot.symbol == "BTCUSDT"
    assert len(snapshot.bids) == 3
    assert len(snapshot.asks) == 3
    # Imbalance should be positive (more bids)
    assert snapshot.imbalance > 0
    assert abs(snapshot.imbalance - 0.176) < 0.01


@pytest.mark.asyncio
async def test_handles_api_error(mock_connector, mock_storage):
    """Should handle API error gracefully."""
    mock_connector._public_request = AsyncMock(
        return_value={"retCode": 10001, "retMsg": "Invalid symbol"}
    )

    collector = OrderbookCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["INVALID"],
    )

    saved = await collector.collect_once()
    assert saved == 0
    assert collector.stats["errors"] == 1
```

### Manual Test

```bash
# Activate venv
source .venv/bin/activate

# Run collector for 30 seconds
timeout 30 python scripts/run_delta_collector.py --orderbook --interval 5

# Check database
psql -d trading_platform -c "SELECT COUNT(*) FROM orderbook_snapshots;"

psql -d trading_platform -c "
  SELECT symbol, imbalance, timestamp 
  FROM orderbook_snapshots 
  ORDER BY timestamp DESC 
  LIMIT 5;
"
```

---

## ⚠️ Важно

1. **Используй существующий BaseCollector** — уже реализован в DELTA-001
2. **Проверь OrderbookSnapshotModel** — может потребоваться настройка JSONB сериализации
3. **Interval = 5 секунд** — чаще чем trades (10s), т.к. orderbook меняется быстро
4. **API limit = 25** — Bybit не поддерживает limit=20, используй 25 и обрезай до 20
5. **Imbalance range** — от -1.0 до +1.0

---

## 📋 Checklist перед сдачей

- [ ] Файл `orderbook_collector.py` создан
- [ ] Класс наследует `BaseCollector`
- [ ] `__init__.py` обновлён с экспортом
- [ ] CLI скрипт поддерживает `--orderbook`
- [ ] Imbalance рассчитывается корректно
- [ ] Unit test проходит
- [ ] Manual test: данные появляются в БД
- [ ] Логирование работает

---

## 🚀 Следующий шаг

После выполнения → **DELTA-003** (OpenInterestCollector)

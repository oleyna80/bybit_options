# 🎯 Задача: DELTA-003 — REST-based OpenInterestCollector

**Статус:** 🟡 READY FOR EXECUTION  
**Приоритет:** MEDIUM  
**Оценка времени:** 1-2 часа  
**Исполнитель:** Backend Developer  
**Зависит от:** DELTA-001 (LargeTradeCollector) — должна быть выполнена ✅

---

## 📋 Контекст

Мы внедряем систему **Delta Volume Analytics** для сбора и анализа объёмной дельты. DELTA-001 (Trades) и DELTA-002 (Orderbook) уже реализованы. Теперь нужен сбор Открытого Интереса (Open Interest).

**Полное ТЗ проекта:** [delta_volume_analytics.tz.md](delta_volume_analytics.tz.md)  
**Предыдущая задача:** [DELTA-002.task.md](DELTA-002.task.md) ✅

**Текущая задача:** Создать collector для сбора Open Interest через REST API (polling каждую минуту).

---

## 🎯 Цель

Создать `OpenInterestCollector` — сервис для сбора Open Interest (OI) с Bybit через REST API и сохранения в TimescaleDB.

**Ключевые характеристики:**
- REST polling каждые 60 секунд (default)
- Сбор OI для BTCUSDT и ETHUSDT
- Расчёт изменения OI не требуется на уровне Collector (будет в Analyzer), но можно логировать.

---

## ✅ Acceptance Criteria

- [ ] AC1: Создан файл `open_interest_collector.py` в директории `collectors/`
- [ ] AC2: Класс `OpenInterestCollector` наследует `BaseCollector`
- [ ] AC3: Collector использует Bybit REST API `/v5/market/open-interest`
- [ ] AC4: Polling интервал 60 секунд (конфигурируемый)
- [ ] AC5: Сохранение в таблицу `open_interest` (уже существует)
- [ ] AC6: CLI опция `--oi` в `run_delta_collector.py`
- [ ] AC7: Тест проходит
- [ ] AC8: Совместный запуск `--trades --orderbook --oi`

---

## 📁 Файлы

### Создать:

```
bybit_options/services/delta/collectors/open_interest_collector.py
tests/test_delta/test_open_interest_collector.py
```

### Изменить:

```
bybit_options/services/delta/collectors/__init__.py  # Добавить экспорт
scripts/run_delta_collector.py                        # Добавить --oi логику
```

### Существующие (использовать):

```
bybit_options/services/delta/collectors/base_collector.py   # Наследоваться
bybit_options/services/bybit_connector.py                   # BybitConnector
bybit_options/models/delta_models.py                        # OpenInterestModel (нужно проверить/создать)
bybit_options/services/delta/storage_service.py             # StorageService (добавить save_open_interest)
bybit_options/services/delta/database_config.py             # db connection
```

---

## 🏗️ Архитектура

### Схема

```
┌─────────────────────────────────────────────────────────────┐
│                   OpenInterestCollector                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │BybitConnector│───►│OI Collector      │───►│StorageService│
│  │/v5/market/   │    │ - fetch OI       │    │save_open_  │
│  │open-interest │    │                  │    │interest()  │
│  └─────────────┘    └──────────────────┘    └───────────┘  │
│                              │                              │
│                              ▼                              │
│                     ┌───────────────┐                       │
│                     │  TimescaleDB  │                       │
│                     │ open_interest │                       │
│                     └───────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Every 60 seconds:
   ├── GET /v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=5min&limit=1
   ├── GET /v5/market/open-interest?category=linear&symbol=ETHUSDT&intervalTime=5min&limit=1
   │
2. Parse response:
   │   "openInterest": "45000.123"
   │   "timestamp": "1705702800000"
   │
3. Create OpenInterestModel
   │
4. Save to TimescaleDB
   │
5. Log stats
```

---

## 🔌 Bybit API Reference

### Endpoint: /v5/market/open-interest

```
GET https://api.bybit.com/v5/market/open-interest

Parameters:
- category: linear | inverse
- symbol: BTCUSDT
- intervalTime: 5min | 15min | 30min | 1h | 4h | 1d (default 5min)
- limit: 1-200 (default 50)

Response:
{
  "retCode": 0,
  "result": {
    "symbol": "BTCUSDT",
    "category": "linear",
    "list": [
      {
        "openInterest": "50005.12",
        "timestamp": "1705702800000"
      },
      ...
    ]
  }
}
```

---

## 📝 Спецификации классов

### OpenInterestCollector

```python
# bybit_options/services/delta/collectors/open_interest_collector.py

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from loguru import logger

from bybit_options.models.delta_models import OpenInterestModel
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.storage_service import StorageService
from .base_collector import BaseCollector


class OpenInterestCollector(BaseCollector):
    """
    Collector for Open Interest from Bybit REST API.
    
    Features:
    - Polls /v5/market/open-interest every N seconds (default 60)
    - Saves to TimescaleDB
    """
    
    DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]

    def __init__(
        self,
        connector: BybitConnector,
        storage: StorageService,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 60,
        category: str = "linear",
    ) -> None:
        super().__init__(interval_seconds=interval_seconds)
        self.connector = connector
        self.storage = storage
        self.symbols = symbols or self.DEFAULT_SYMBOLS
        self.category = category

    async def collect_once(self) -> int:
        """Execute one collection cycle."""
        items: List[OpenInterestModel] = []
        
        for symbol in self.symbols:
            try:
                # Get LATEST OI (limit=1)
                data = await self.connector.get_open_interest(
                    symbol=symbol,
                    category=self.category,
                    interval="5min",
                    limit=1
                )
                
                # Bybit returns a LIST, we need the latest one
                if data and isinstance(data, list) and len(data) > 0:
                    latest = data[0]
                    items.append(latest)
            
            except Exception as exc:
                self.stats["errors"] += 1
                logger.error(f"❌ Error fetching OI for {symbol}: {exc}")
        
        if not items:
            return 0
            
        self.stats['items_collected'] += len(items)
        saved = await self.storage.save_open_interest(items)
        
        if saved > 0:
            for item in items:
                logger.debug(f"📊 {item.symbol} OI: {item.open_interest}")
                
        return saved
```

### Модификации BybitConnector

Добавить метод `get_open_interest` если его нет.

```python
    async def get_open_interest(
        self,
        symbol: str,
        category: str = "linear",
        interval: str = "5min",
        limit: int = 1
    ) -> List[OpenInterestModel]:
        # ... logic ...
```

### Модификации StorageService

Добавить метод `save_open_interest`.

```python
    async def save_open_interest(self, items: List[OpenInterestModel]) -> int:
        # ... batch insert logic ...
```

---

## 🧪 Testing

### Unit Test

```python
# tests/test_delta/test_open_interest_collector.py

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from bybit_options.services.delta.collectors.open_interest_collector import (
    OpenInterestCollector,
)

# ... fixtures & tests similar to other collectors ...
```

---

## 📋 Checklist перед сдачей

- [ ] Файл `open_interest_collector.py` создан
- [ ] `BybitConnector` обновлён (если нужно)
- [ ] `StorageService` обновлён
- [ ] CLI скрипт поддерживает `--oi`
- [ ] Unit test проходит
- [ ] Manual test: данные появляются в БД

---

## 🚀 Следующий шаг

После выполнения → **DELTA-005** (DeltaAnalyzer) - уже интереснее, расчёт метрик!

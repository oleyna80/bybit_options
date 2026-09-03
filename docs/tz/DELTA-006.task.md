# 🎯 Задача: DELTA-006 — FractalEnricher (Async)

**Статус:** 🟡 READY FOR EXECUTION  
**Приоритет:** MEDIUM  
**Оценка времени:** 2-3 часа  
**Исполнитель:** Backend Developer  
**Зависит от:** DELTA-005 (DeltaAnalyzer) — должна быть выполнена ✅

---

## 📋 Контекст

Fractal Collector уже работает и сохраняет фракталы в `fractals_cache`. Теперь нужен **асинхронный enricher**, который будет периодически обогащать ключевые фракталы Delta-метриками из `DeltaAnalyzer`.

**Полное ТЗ проекта:** [delta_volume_analytics.tz.md](delta_volume_analytics.tz.md)  
**Предыдущая задача:** DELTA-005 (DeltaAnalyzer) ✅

**Текущая задача:** Создать `FractalEnricher` — cron-сервис для обогащения фракталов Delta-данными.

---

## 🎯 Цель

Создать `FractalEnricher` — сервис, который:
1. Запускается по расписанию (каждые 5 минут)
2. Находит фракталы без Delta-данных
3. Обогащает их метриками из `DeltaAnalyzer`
4. Обновляет `fractals_cache`

**Ключевые характеристики:**
- Асинхронный (не блокирует основной Fractal Collector)
- Обогащает только ключевые фракталы (`is_key_fractal = true`)
- Добавляет confidence score

---

## ✅ Acceptance Criteria

- [ ] AC1: Создана миграция `009_extend_fractals_delta.sql`
- [ ] AC2: Добавлены поля: `delta_1h`, `delta_4h`, `delta_24h`, `oi_delta_24h`, `orderbook_imbalance`, `confidence_score`
- [ ] AC3: Класс `FractalEnricher` реализован
- [ ] AC4: Метод `enrich_fractals()` обогащает фракталы
- [ ] AC5: Расчёт `confidence_score` (простая логика для MVP)
- [ ] AC6: CLI скрипт `run_fractal_enricher.py`
- [ ] AC7: Systemd service + timer
- [ ] AC8: Unit tests проходят

---

## 📁 Файлы

### Создать:

```
database_migrations/009_extend_fractals_delta.sql
bybit_options/services/delta/enricher.py
scripts/run_fractal_enricher.py
scripts/systemd/bybit-fractal-enricher.service
scripts/systemd/bybit-fractal-enricher.timer
tests/test_delta/test_enricher.py
```

### Существующие (использовать):

```
bybit_options/services/delta/analyzer.py         # DeltaAnalyzer
bybit_options/services/delta/database_config.py  # db connection
```

---

## 🏗️ Архитектура

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     FractalEnricher                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────────┐                │
│  │ fractals_    │─────►│ FractalEnricher  │                │
│  │ cache        │      │ - find unenriched│                │
│  │ (is_key=true)│      │ - call Analyzer  │                │
│  └──────────────┘      │ - calc confidence│                │
│                        │ - update DB      │                │
│                        └──────────────────┘                │
│                                 │                           │
│                                 ▼                           │
│                        ┌──────────────────┐                │
│                        │ DeltaAnalyzer    │                │
│                        │ - hourly delta   │                │
│                        │ - OI change      │                │
│                        │ - imbalance      │                │
│                        └──────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Cron: Every 5 minutes (systemd timer)
```

---

## 📝 Спецификации

### 1. Database Migration

```sql
-- database_migrations/009_extend_fractals_delta.sql

-- Add Delta enrichment columns to fractals_cache
ALTER TABLE fractals_cache
ADD COLUMN IF NOT EXISTS delta_1h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS delta_4h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS delta_24h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS oi_delta_24h NUMERIC(20, 8),
ADD COLUMN IF NOT EXISTS orderbook_imbalance NUMERIC(5, 4),
ADD COLUMN IF NOT EXISTS confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMPTZ;

-- Index for finding unenriched fractals
CREATE INDEX IF NOT EXISTS idx_fractals_unenriched
ON fractals_cache (is_key_fractal, enriched_at)
WHERE is_key_fractal = true AND enriched_at IS NULL;

COMMENT ON COLUMN fractals_cache.delta_1h IS 'Filtered delta over 1 hour';
COMMENT ON COLUMN fractals_cache.delta_4h IS 'Filtered delta over 4 hours';
COMMENT ON COLUMN fractals_cache.delta_24h IS 'Filtered delta over 24 hours';
COMMENT ON COLUMN fractals_cache.oi_delta_24h IS 'Open Interest change over 24 hours';
COMMENT ON COLUMN fractals_cache.orderbook_imbalance IS 'Average orderbook imbalance';
COMMENT ON COLUMN fractals_cache.confidence_score IS 'Signal confidence 0-100';
```

### 2. FractalEnricher Class

```python
# bybit_options/services/delta/enricher.py

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Optional

from loguru import logger

from bybit_options.services.delta.analyzer import DeltaAnalyzer
from bybit_options.services.delta.database_config import db


class FractalEnricher:
    """
    Asynchronous enricher for key fractals with Delta metrics.
    
    Features:
    - Runs periodically (cron/systemd timer)
    - Enriches only key fractals (is_key_fractal = true)
    - Adds delta metrics, OI change, orderbook imbalance
    - Calculates confidence score
    """

    def __init__(self, exchange: str = "bybit"):
        self.exchange = exchange
        self.analyzer = DeltaAnalyzer(exchange=exchange)
        self.stats = {
            "fractals_found": 0,
            "fractals_enriched": 0,
            "errors": 0
        }

    async def find_unenriched_fractals(self, limit: int = 50) -> List[Dict]:
        """
        Find key fractals that need enrichment.
        
        Returns:
            List of fractal records
        """
        query = """
            SELECT
                id, timestamp, timeframe, base_coin, type,
                price, symbol, candle_time, fractal_type
            FROM fractals_cache
            WHERE is_key_fractal = true
              AND enriched_at IS NULL
            ORDER BY timestamp DESC
            LIMIT $1
        """
        
        async with db.acquire() as conn:
            rows = await conn.fetch(query, limit)
            
        return [dict(row) for row in rows]

    async def enrich_fractal(self, fractal: Dict) -> Dict:
        """
        Enrich a single fractal with Delta metrics.
        
        Returns:
            Dict with enrichment data
        """
        symbol = fractal.get("symbol") or f"{fractal['base_coin']}USDT"
        
        try:
            # Get Delta metrics
            delta_1h = await self.analyzer.get_hourly_delta(symbol, hours=1)
            delta_4h = await self.analyzer.get_hourly_delta(symbol, hours=4)
            delta_24h = await self.analyzer.get_hourly_delta(symbol, hours=24)
            
            # Get OI change
            oi_change = await self.analyzer.get_oi_change(symbol, hours=24)
            
            # Get orderbook imbalance
            imbalance = await self.analyzer.get_orderbook_imbalance(symbol, minutes=5)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                fractal, delta_1h, delta_4h, delta_24h, oi_change, imbalance
            )
            
            return {
                "delta_1h": delta_1h["filtered_delta"],
                "delta_4h": delta_4h["filtered_delta"],
                "delta_24h": delta_24h["filtered_delta"],
                "oi_delta_24h": oi_change.get("oi_change"),
                "orderbook_imbalance": imbalance["avg_imbalance"],
                "confidence_score": confidence,
                "enriched_at": datetime.now(timezone.utc)
            }
            
        except Exception as exc:
            logger.error(f"Failed to enrich fractal {fractal['id']}: {exc}")
            raise

    def _calculate_confidence(
        self,
        fractal: Dict,
        delta_1h: Dict,
        delta_4h: Dict,
        delta_24h: Dict,
        oi_change: Dict,
        imbalance: Dict
    ) -> int:
        """
        Calculate confidence score (0-100) for fractal signal.
        
        MVP Logic:
        - Bullish fractal + positive delta = +30
        - Bearish fractal + negative delta = +30
        - OI increase = +20
        - Orderbook imbalance aligned = +20
        - Strong delta (>threshold) = +30
        """
        score = 0
        fractal_type = fractal.get("type") or fractal.get("fractal_type")
        
        # Delta alignment (30 points)
        delta = delta_1h["filtered_delta"]
        if fractal_type == "up" and delta > 0:
            score += 30
        elif fractal_type == "down" and delta < 0:
            score += 30
            
        # OI increase (20 points)
        oi_delta = oi_change.get("oi_change")
        if oi_delta and oi_delta > 0:
            score += 20
            
        # Orderbook imbalance (20 points)
        imb = imbalance["avg_imbalance"]
        if fractal_type == "up" and imb > Decimal("0.1"):
            score += 20
        elif fractal_type == "down" and imb < Decimal("-0.1"):
            score += 20
            
        # Strong delta (30 points)
        if abs(delta) > Decimal("10"):  # Threshold for BTC
            score += 30
            
        return min(score, 100)

    async def update_fractal(self, fractal_id: int, enrichment: Dict) -> bool:
        """Update fractal with enrichment data."""
        query = """
            UPDATE fractals_cache
            SET
                delta_1h = $1,
                delta_4h = $2,
                delta_24h = $3,
                oi_delta_24h = $4,
                orderbook_imbalance = $5,
                confidence_score = $6,
                enriched_at = $7
            WHERE id = $8
        """
        
        try:
            async with db.acquire() as conn:
                await conn.execute(
                    query,
                    enrichment["delta_1h"],
                    enrichment["delta_4h"],
                    enrichment["delta_24h"],
                    enrichment["oi_delta_24h"],
                    enrichment["orderbook_imbalance"],
                    enrichment["confidence_score"],
                    enrichment["enriched_at"],
                    fractal_id
                )
            return True
        except Exception as exc:
            logger.error(f"Failed to update fractal {fractal_id}: {exc}")
            return False

    async def run_once(self) -> Dict:
        """Run one enrichment cycle."""
        logger.info("🔄 Starting fractal enrichment cycle")
        
        fractals = await self.find_unenriched_fractals(limit=50)
        self.stats["fractals_found"] = len(fractals)
        
        if not fractals:
            logger.info("✅ No fractals to enrich")
            return self.stats
            
        logger.info(f"📋 Found {len(fractals)} fractals to enrich")
        
        for fractal in fractals:
            try:
                enrichment = await self.enrich_fractal(fractal)
                success = await self.update_fractal(fractal["id"], enrichment)
                
                if success:
                    self.stats["fractals_enriched"] += 1
                    logger.info(
                        f"✅ Enriched fractal {fractal['id']} "
                        f"(confidence: {enrichment['confidence_score']})"
                    )
                    
            except Exception as exc:
                self.stats["errors"] += 1
                logger.error(f"❌ Error enriching fractal {fractal['id']}: {exc}")
                
        logger.info(
            f"🏁 Enrichment complete: {self.stats['fractals_enriched']}/{len(fractals)} "
            f"enriched, {self.stats['errors']} errors"
        )
        
        return self.stats
```

### 3. CLI Script

```python
# scripts/run_fractal_enricher.py

#!/usr/bin/env python3
"""Fractal Enricher CLI - runs enrichment cycle."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from bybit_options.services.delta.enricher import FractalEnricher
from bybit_options.services.delta.database_config import db


async def main():
    """Run one enrichment cycle."""
    try:
        await db.connect()
        
        enricher = FractalEnricher()
        stats = await enricher.run_once()
        
        logger.info(f"📊 Stats: {stats}")
        
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Systemd Service

```ini
# scripts/systemd/bybit-fractal-enricher.service

[Unit]
Description=Bybit Fractal Enricher
After=network.target postgresql.service

[Service]
Type=oneshot
User=dmitrii
WorkingDirectory=/home/dmitrii/projects/bybit_options
Environment="PATH=/home/dmitrii/projects/bybit_options/.venv/bin:/usr/bin"
ExecStart=/home/dmitrii/projects/bybit_options/.venv/bin/python scripts/run_fractal_enricher.py

[Install]
WantedBy=multi-user.target
```

### 5. Systemd Timer

```ini
# scripts/systemd/bybit-fractal-enricher.timer

[Unit]
Description=Run Fractal Enricher every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 🧪 Testing

```python
# tests/test_delta/test_enricher.py

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

from bybit_options.services.delta.enricher import FractalEnricher


@pytest.mark.asyncio
async def test_calculate_confidence_bullish():
    """Test confidence calculation for bullish fractal."""
    enricher = FractalEnricher()
    
    fractal = {"type": "up"}
    delta_1h = {"filtered_delta": Decimal("15")}  # Positive + strong
    delta_4h = {"filtered_delta": Decimal("20")}
    delta_24h = {"filtered_delta": Decimal("30")}
    oi_change = {"oi_change": Decimal("1000")}  # Positive
    imbalance = {"avg_imbalance": Decimal("0.15")}  # Positive
    
    score = enricher._calculate_confidence(
        fractal, delta_1h, delta_4h, delta_24h, oi_change, imbalance
    )
    
    # 30 (alignment) + 20 (OI) + 20 (imbalance) + 30 (strong) = 100
    assert score == 100
```

---

## 📋 Checklist перед сдачей

- [ ] Миграция 009 создана и применена
- [ ] `FractalEnricher` реализован
- [ ] CLI скрипт работает
- [ ] Systemd service + timer созданы
- [ ] Unit tests проходят
- [ ] Можно запустить вручную: `python scripts/run_fractal_enricher.py`

---

## 🚀 Следующий шаг

После выполнения → **DELTA-008** (API Endpoints) для фронтенда

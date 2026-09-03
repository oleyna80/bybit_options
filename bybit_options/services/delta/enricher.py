"""Asynchronous enricher for key fractals with Delta metrics."""

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

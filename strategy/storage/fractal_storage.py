"""
Fractal storage for Fractal Collector (FRAC-003).
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import asyncpg


class FractalStorage:
    """Async storage layer for fractals_cache with upsert + retention."""

    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self._db_pool = db_pool

    async def upsert_fractals(self, fractals: Sequence[Mapping]) -> int:
        if not fractals:
            return 0

        normalized = [self._normalize_fractal(fractal) for fractal in fractals]

        symbols = [item["symbol"] for item in normalized]
        timeframes = [item["timeframe"] for item in normalized]
        fractal_types = [item["fractal_type"] for item in normalized]
        prices = [item["price"] for item in normalized]
        candle_times = [item["candle_time"] for item in normalized]
        bb_upper_1 = [item.get("bb_upper_1sigma") for item in normalized]
        bb_lower_1 = [item.get("bb_lower_1sigma") for item in normalized]
        bb_upper_2 = [item.get("bb_upper_2sigma") for item in normalized]
        bb_lower_2 = [item.get("bb_lower_2sigma") for item in normalized]
        teeth = [item.get("alligator_teeth") for item in normalized]
        is_key = [item.get("is_key_fractal") for item in normalized]
        base_coins = [item.get("base_coin") for item in normalized]
        timestamps = [item.get("timestamp") for item in normalized]
        legacy_types = [item.get("type") for item in normalized]

        query = """
            INSERT INTO fractals_cache (
                symbol,
                timeframe,
                fractal_type,
                price,
                candle_time,
                bb_upper_1sigma,
                bb_lower_1sigma,
                bb_upper_2sigma,
                bb_lower_2sigma,
                alligator_teeth,
                is_key_fractal,
                base_coin,
                timestamp,
                type
            )
            SELECT * FROM UNNEST(
                $1::text[],
                $2::text[],
                $3::text[],
                $4::numeric[],
                $5::timestamptz[],
                $6::numeric[],
                $7::numeric[],
                $8::numeric[],
                $9::numeric[],
                $10::numeric[],
                $11::boolean[],
                $12::text[],
                $13::timestamptz[],
                $14::text[]
            )
            ON CONFLICT (symbol, timeframe, fractal_type, candle_time)
            DO UPDATE SET
                price = EXCLUDED.price,
                is_key_fractal = EXCLUDED.is_key_fractal,
                bb_upper_1sigma = EXCLUDED.bb_upper_1sigma,
                bb_lower_1sigma = EXCLUDED.bb_lower_1sigma,
                bb_upper_2sigma = EXCLUDED.bb_upper_2sigma,
                bb_lower_2sigma = EXCLUDED.bb_lower_2sigma,
                alligator_teeth = EXCLUDED.alligator_teeth
            RETURNING id
        """

        async with self._db_pool.acquire() as conn:
            async with conn.transaction():
                records = await conn.fetch(
                    query,
                    symbols,
                    timeframes,
                    fractal_types,
                    prices,
                    candle_times,
                    bb_upper_1,
                    bb_lower_1,
                    bb_upper_2,
                    bb_lower_2,
                    teeth,
                    is_key,
                    base_coins,
                    timestamps,
                    legacy_types,
                )
                processed = len(records)

                pairs = {(item["symbol"], item["timeframe"]) for item in normalized}
                for symbol, timeframe in pairs:
                    await self._prune_retention(conn, symbol=symbol, timeframe=timeframe, limit=100)

        return processed

    async def fetch_existing_keys(
        self,
        keys: Sequence[tuple[str, str, str, "datetime"]],
    ) -> set[tuple[str, str, str, "datetime"]]:
        if not keys:
            return set()

        symbols, timeframes, fractal_types, candle_times = zip(*keys)
        query = """
            WITH keys AS (
                SELECT * FROM UNNEST(
                    $1::text[],
                    $2::text[],
                    $3::text[],
                    $4::timestamptz[]
                ) AS t(symbol, timeframe, fractal_type, candle_time)
            )
            SELECT f.symbol, f.timeframe, f.fractal_type, f.candle_time
            FROM fractals_cache f
            JOIN keys k
              ON f.symbol = k.symbol
             AND f.timeframe = k.timeframe
             AND f.fractal_type = k.fractal_type
             AND f.candle_time = k.candle_time
        """

        async with self._db_pool.acquire() as conn:
            rows = await conn.fetch(query, symbols, timeframes, fractal_types, candle_times)

        return {
            (row["symbol"], row["timeframe"], row["fractal_type"], row["candle_time"])
            for row in rows
        }

    async def upsert_fractal(self, fractal: Mapping) -> None:
        await self.upsert_fractals([fractal])

    async def prune_retention(self, symbol: str, timeframe: str, limit: int = 100) -> int:
        async with self._db_pool.acquire() as conn:
            async with conn.transaction():
                return await self._prune_retention(conn, symbol=symbol, timeframe=timeframe, limit=limit)

    @staticmethod
    async def _prune_retention(
        conn: asyncpg.Connection,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> int:
        delete_query = """
            DELETE FROM fractals_cache
            WHERE symbol = $1
              AND timeframe = $2
              AND candle_time < (
                  SELECT candle_time
                  FROM fractals_cache
                  WHERE symbol = $1 AND timeframe = $2
                  ORDER BY candle_time DESC
                  OFFSET $3
                  LIMIT 1
              )
        """
        status = await conn.execute(delete_query, symbol, timeframe, limit)
        return int(status.split()[-1]) if status else 0

    @staticmethod
    def _normalize_fractal(fractal: Mapping) -> dict:
        symbol = fractal.get("symbol")
        timeframe = fractal.get("timeframe")
        fractal_type = fractal.get("fractal_type")
        price = fractal.get("price")
        candle_time = fractal.get("candle_time")

        if not symbol or not timeframe or not fractal_type or price is None or candle_time is None:
            raise ValueError("fractal must include symbol, timeframe, fractal_type, price, candle_time")

        legacy_type = fractal.get("type")
        if legacy_type is None:
            legacy_type = "HIGH" if fractal_type.upper() == "UP" else "LOW"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "fractal_type": fractal_type,
            "price": price,
            "candle_time": candle_time,
            "bb_upper_1sigma": fractal.get("bb_upper_1sigma"),
            "bb_lower_1sigma": fractal.get("bb_lower_1sigma"),
            "bb_upper_2sigma": fractal.get("bb_upper_2sigma"),
            "bb_lower_2sigma": fractal.get("bb_lower_2sigma"),
            "alligator_teeth": fractal.get("alligator_teeth"),
            "is_key_fractal": fractal.get("is_key_fractal", False),
            "base_coin": fractal.get("base_coin", symbol.replace("USDT", "")),
            "timestamp": fractal.get("timestamp", candle_time),
            "type": legacy_type,
        }

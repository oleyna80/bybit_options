"""
Storage Service for Delta Analytics
===================================
Сервис для сохранения Delta данных в БД с batch inserts.
"""

import json
from typing import List
from datetime import datetime
from loguru import logger

from bybit_options.models.delta_models import (
    LargeTradeModel,
    OrderbookSnapshotModel
)
from bybit_options.services.delta.database_config import db


class StorageService:
    """
    Сервис для сохранения Delta данных.
    
    Features:
    - Batch inserts для производительности
    - Автоматическая дедупликация (ON CONFLICT DO NOTHING)
    - Error handling и retry логика
    - Статистика сохранённых записей
    
    Usage:
        storage = StorageService()
        await storage.save_large_trades([trade1, trade2, ...])
    """
    
    def __init__(self):
        self.stats = {
            'trades_saved': 0,
            'trades_duplicates': 0,
            'orderbooks_saved': 0,
            'errors': 0
        }
    
    async def save_large_trades(
        self,
        trades: List[LargeTradeModel]
    ) -> int:
        """
        Сохранить список крупных сделок в БД.
        
        Args:
            trades: Список LargeTradeModel
        
        Returns:
            Количество успешно сохранённых записей
        
        Note:
            Использует batch insert для производительности.
            Дубликаты игнорируются (ON CONFLICT DO NOTHING).
        """
        if not trades:
            return 0
        
        try:
            # Подготовка данных для batch insert
            values = [
                (
                    trade.exchange,
                    trade.market_type,
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.side,
                    trade.trade_id,
                    trade.timestamp
                )
                for trade in trades
            ]
            
            # Batch insert с ON CONFLICT DO NOTHING
            query = """
                INSERT INTO large_trades (
                    exchange, market_type, symbol, price, quantity,
                    side, trade_id, timestamp
                )
                SELECT * FROM UNNEST($1::text[], $2::text[], $3::text[],
                                     $4::numeric[], $5::numeric[], $6::text[],
                                     $7::text[], $8::timestamptz[])
                ON CONFLICT (timestamp, exchange, trade_id) DO NOTHING
            """
            
            # Транспонируем данные для UNNEST
            exchanges = [v[0] for v in values]
            market_types = [v[1] for v in values]
            symbols = [v[2] for v in values]
            prices = [v[3] for v in values]
            quantities = [v[4] for v in values]
            sides = [v[5] for v in values]
            trade_ids = [v[6] for v in values]
            timestamps = [v[7] for v in values]
            
            async with db.acquire() as conn:
                result = await conn.execute(
                    query,
                    exchanges, market_types, symbols, prices,
                    quantities, sides, trade_ids, timestamps
                )

            try:
                saved_count = int(result.split()[-1]) if result else 0
            except (ValueError, IndexError):
                saved_count = 0
            duplicates = len(trades) - saved_count
            
            self.stats['trades_saved'] += saved_count
            self.stats['trades_duplicates'] += duplicates
            
            logger.info(
                f"💾 Saved {saved_count} trades, "
                f"skipped {duplicates} duplicates"
            )
            
            return saved_count
        
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Failed to save trades: {e}")
            raise
    
    async def save_orderbook_snapshot(
        self,
        snapshot: OrderbookSnapshotModel
    ) -> bool:
        """
        Сохранить orderbook snapshot в БД.
        
        Args:
            snapshot: OrderbookSnapshotModel
        
        Returns:
            True если успешно сохранено
        """
        saved = await self.save_orderbook_snapshots([snapshot])
        return saved > 0

    async def save_orderbook_snapshots(
        self,
        snapshots: List[OrderbookSnapshotModel]
    ) -> int:
        """
        Batch сохранение orderbook snapshots в БД.

        Args:
            snapshots: Список OrderbookSnapshotModel

        Returns:
            Количество успешно сохранённых записей
        """
        if not snapshots:
            return 0

        try:
            values = [
                (
                    snapshot.exchange,
                    snapshot.symbol,
                    snapshot.timestamp,
                    json.dumps([
                        [str(level.price), str(level.size)]
                        for level in snapshot.bids
                    ]),
                    json.dumps([
                        [str(level.price), str(level.size)]
                        for level in snapshot.asks
                    ]),
                    snapshot.bid_volume_total,
                    snapshot.ask_volume_total,
                    snapshot.imbalance,
                )
                for snapshot in snapshots
            ]

            exchanges = [v[0] for v in values]
            symbols = [v[1] for v in values]
            timestamps = [v[2] for v in values]
            bids_json = [v[3] for v in values]
            asks_json = [v[4] for v in values]
            bid_totals = [v[5] for v in values]
            ask_totals = [v[6] for v in values]
            imbalances = [v[7] for v in values]

            query = """
                INSERT INTO orderbook_snapshots (
                    exchange, symbol, timestamp,
                    bids, asks,
                    bid_volume_total, ask_volume_total, imbalance
                )
                SELECT * FROM UNNEST(
                    $1::text[],
                    $2::text[],
                    $3::timestamptz[],
                    $4::jsonb[],
                    $5::jsonb[],
                    $6::numeric[],
                    $7::numeric[],
                    $8::numeric[]
                )
                ON CONFLICT (timestamp, exchange, symbol) DO NOTHING
            """

            async with db.acquire() as conn:
                result = await conn.execute(
                    query,
                    exchanges,
                    symbols,
                    timestamps,
                    bids_json,
                    asks_json,
                    bid_totals,
                    ask_totals,
                    imbalances,
                )

            try:
                saved_count = int(result.split()[-1]) if result else 0
            except (ValueError, IndexError):
                saved_count = 0

            self.stats['orderbooks_saved'] += saved_count
            duplicates = len(snapshots) - saved_count

            logger.info(
                f"💾 Saved {saved_count} orderbook snapshots, "
                f"skipped {duplicates} duplicates"
            )

            return saved_count

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Failed to save orderbooks: {e}")
            raise

    async def save_open_interest(self, items: List['OpenInterestModel']) -> int:
        """
        Batch save Open Interest data.
        """
        if not items:
            return 0
            
        try:
            values = [
                (
                    item.exchange,
                    item.symbol,
                    item.open_interest,
                    item.timestamp
                )
                for item in items
            ]
            
            exchanges = [v[0] for v in values]
            symbols = [v[1] for v in values]
            ois = [v[2] for v in values]
            timestamps = [v[3] for v in values]
            
            query = """
                INSERT INTO open_interest (
                    exchange, symbol, open_interest, timestamp
                )
                SELECT * FROM UNNEST(
                    $1::text[],
                    $2::text[],
                    $3::numeric[],
                    $4::timestamptz[]
                )
                ON CONFLICT (timestamp, exchange, symbol) DO NOTHING
            """
            
            async with db.acquire() as conn:
                result = await conn.execute(
                    query,
                    exchanges, symbols, ois, timestamps
                )
                
            try:
                saved_count = int(result.split()[-1]) if result else 0
            except (ValueError, IndexError):
                saved_count = 0
                
            if 'oi_saved' not in self.stats:
                self.stats['oi_saved'] = 0
            self.stats['oi_saved'] += saved_count
            
            logger.info(f"💾 Saved {saved_count} OI records")
            return saved_count
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Failed to save OI: {e}")
            return 0

    
    async def get_latest_trades(
        self,
        exchange: str,
        symbol: str,
        limit: int = 100
    ) -> List[dict]:
        """
        Получить последние сохранённые сделки.
        
        Args:
            exchange: Название биржи
            symbol: Символ инструмента
            limit: Максимум записей
        
        Returns:
            Список словарей с данными сделок
        """
        query = """
            SELECT 
                exchange, market_type, symbol, price, quantity,
                side, trade_id, timestamp
            FROM large_trades
            WHERE exchange = $1 AND symbol = $2
            ORDER BY timestamp DESC
            LIMIT $3
        """
        
        try:
            async with db.acquire() as conn:
                records = await conn.fetch(query, exchange, symbol, limit)
            
            return [dict(record) for record in records]
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch trades: {e}")
            return []
    
    async def get_latest_orderbook(
        self,
        exchange: str,
        symbol: str
    ) -> dict | None:
        """
        Получить последний сохранённый orderbook snapshot.
        
        Args:
            exchange: Название биржи
            symbol: Символ инструмента
        
        Returns:
            Словарь с данными orderbook или None
        """
        query = """
            SELECT 
                exchange, symbol, timestamp,
                bids, asks,
                bid_volume_total, ask_volume_total, imbalance
            FROM orderbook_snapshots
            WHERE exchange = $1 AND symbol = $2
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        try:
            async with db.acquire() as conn:
                record = await conn.fetchrow(query, exchange, symbol)
            
            return dict(record) if record else None
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch orderbook: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Получить статистику работы сервиса"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Сбросить статистику"""
        self.stats = {
            'trades_saved': 0,
            'trades_duplicates': 0,
            'orderbooks_saved': 0,
            'errors': 0
        }

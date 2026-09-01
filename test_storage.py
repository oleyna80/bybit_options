"""
Тест Storage Service
"""

import asyncio
import os
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv

# Загрузи .env
load_dotenv()

from bybit_options.services.delta import db, StorageService
from bybit_options.models.delta_models import LargeTradeModel, OrderbookSnapshotModel

async def test_storage():
    print("=" * 70)
    print("ТЕСТ STORAGE SERVICE")
    print("=" * 70)
    
    # Подключение к БД
    print("\n1. Подключение к БД...")
    try:
        await db.connect()
        print("✅ Подключение успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Создание storage service
    storage = StorageService()
    
    # Тест 1: Сохранение trades
    print("\n2. Тест сохранения trades...")
    try:
        test_trades = [
            LargeTradeModel(
                exchange='bybit',
                market_type='spot',
                symbol='BTCUSDT',
                price=Decimal('95000.50'),
                quantity=Decimal('10.5'),
                side='Buy',
                trade_id=f'test_{i}',
                timestamp=datetime.now(timezone.utc)
            )
            for i in range(5)
        ]
        
        saved = await storage.save_large_trades(test_trades)
        print(f"✅ Сохранено {saved} trades")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 2: Сохранение orderbook
    print("\n3. Тест сохранения orderbook...")
    try:
        snapshot = OrderbookSnapshotModel.from_raw_orderbook(
            exchange='bybit',
            symbol='BTCUSDT',
            bids_raw=[['95000.5', '2.34'], ['95000.0', '1.50']],
            asks_raw=[['95001.0', '3.21'], ['95001.5', '0.80']],
            timestamp=datetime.now(timezone.utc)
        )
        
        saved = await storage.save_orderbook_snapshot(snapshot)
        if saved:
            print("✅ Orderbook сохранён")
        else:
            print("⚠️  Orderbook уже существует (duplicate)")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Чтение данных
    print("\n4. Тест чтения данных...")
    try:
        trades = await storage.get_latest_trades('bybit', 'BTCUSDT', limit=5)
        print(f"✅ Прочитано {len(trades)} trades")
        
        orderbook = await storage.get_latest_orderbook('bybit', 'BTCUSDT')
        if orderbook:
            print(f"✅ Orderbook прочитан (imbalance: {orderbook['imbalance']})")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Статистика
    print("\n5. Статистика:")
    stats = storage.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Закрытие
    await db.close()
    print("\n✅ Тест завершён")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_storage())

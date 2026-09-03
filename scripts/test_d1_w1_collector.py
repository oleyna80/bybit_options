#!/usr/bin/env python3
"""
Test D1/W1 Fractal Collection
==============================
Verifies that CollectorLoop can process Daily and Weekly fractals.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.telegram_alerter import TelegramAlerter
from bybit_options.services.delta.database_config import DatabaseConfig
from strategy.data.kline_loader import KlineLoader
from strategy.data.fractal_collector import CollectorLoop
from strategy.storage.fractal_storage import FractalStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_d1_w1_collection():
    """Test D1 and W1 fractal collection."""
    api_key = os.getenv("BYBIT_API_KEY", "")
    api_secret = os.getenv("BYBIT_API_SECRET", "")
    
    # Initialize components
    connector = BybitConnector(api_key, api_secret, testnet=False)
    await connector.connect()  # Initialize HTTP session
    
    db = DatabaseConfig()
    await db.connect()
    
    try:
        loader = KlineLoader(connector)
        storage = FractalStorage(db._pool)
        telegram = TelegramAlerter(enabled=False)  # Disable notifications for testing
        
        collector = CollectorLoop(
            symbol="BTCUSDT",
            kline_loader=loader,
            storage=storage,
            telegram_alerter=telegram
        )
        
        print("\n" + "="*60)
        print("Testing D1 (Daily) Fractal Collection")
        print("="*60)
        
        await collector.run_once(["D1"])
        
        # Query database for D1 fractals
        query = """
            SELECT COUNT(*) as count, 
                   COUNT(*) FILTER (WHERE is_key_fractal = true) as key_count
            FROM fractals_cache
            WHERE symbol = $1 AND timeframe = $2
        """
        result = await db.fetch_one(query, "BTCUSDT", "D1")
        
        print(f"✅ D1 Collection Complete")
        print(f"   Total fractals: {result['count']}")
        print(f"   Key fractals: {result['key_count']}")
        
        print("\n" + "="*60)
        print("Testing W1 (Weekly) Fractal Collection")
        print("="*60)
        
        await collector.run_once(["W1"])
        
        # Query database for W1 fractals
        result = await db.fetch_one(query, "BTCUSDT", "W1")
        
        print(f"✅ W1 Collection Complete")
        print(f"   Total fractals: {result['count']}")
        print(f"   Key fractals: {result['key_count']}")
        
        print("\n" + "="*60)
        print("✅ ALL COLLECTION TESTS PASSED")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        await connector.close()
        await db.close()

if __name__ == "__main__":
    success = asyncio.run(test_d1_w1_collection())
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test D1/W1 Kline Loading
========================
Verifies that KlineLoader can fetch Daily and Weekly candles from Bybit.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from bybit_options.services.bybit_connector import BybitConnector
from strategy.data.kline_loader import KlineLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_d1_w1_klines():
    """Test D1 and W1 kline fetching."""
    api_key = os.getenv("BYBIT_API_KEY", "")
    api_secret = os.getenv("BYBIT_API_SECRET", "")
    
    connector = BybitConnector(api_key, api_secret, testnet=False)
    await connector.connect()  # Initialize HTTP session
    
    try:
        loader = KlineLoader(connector)
        
        print("\n" + "="*60)
        print("Testing D1 (Daily) Kline Loading")
        print("="*60)
        
        d1_candles = await loader.load_klines("BTCUSDT", "D1", limit=50)
        
        if not d1_candles:
            print("❌ D1: No candles returned")
            return False
        
        print(f"✅ D1: Fetched {len(d1_candles)} candles")
        print(f"   First candle: {d1_candles[0]['time']} - Close: ${d1_candles[0]['close']}")
        print(f"   Last candle:  {d1_candles[-1]['time']} - Close: ${d1_candles[-1]['close']}")
        
        print("\n" + "="*60)
        print("Testing W1 (Weekly) Kline Loading")
        print("="*60)
        
        w1_candles = await loader.load_klines("BTCUSDT", "W1", limit=50)
        
        if not w1_candles:
            print("❌ W1: No candles returned")
            return False
        
        print(f"✅ W1: Fetched {len(w1_candles)} candles")
        print(f"   First candle: {w1_candles[0]['time']} - Close: ${w1_candles[0]['close']}")
        print(f"   Last candle:  {w1_candles[-1]['time']} - Close: ${w1_candles[-1]['close']}")
        
        print("\n" + "="*60)
        print("✅ ALL KLINE TESTS PASSED")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        await connector.close()

if __name__ == "__main__":
    success = asyncio.run(test_d1_w1_klines())
    exit(0 if success else 1)

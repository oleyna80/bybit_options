"""
Test script to verify auto-connect functionality in VolatilityContextAPI.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_auto_connect():
    print("\n🧪 Testing Auto-Connect logic in VolatilityContextAPI...")
    
    from bybit_options.services.volatility import VolatilityContextAPI
    from bybit_options.services.delta.database_config import db
    
    # Ensure pool is closed initially
    await db.close()
    print("   ✓ Verified DB pool is closed initially")
    
    api = VolatilityContextAPI()
    
    print("   calling get_context() without explicit db.connect()...")
    try:
        context = await api.get_context("BTC")
        print(f"   ✓ Success! Context retrieved with IV: {context.current_iv}")
        
        # Verify pool is actually open now
        if db._pool is not None:
             print("   ✓ DB pool was automatically opened")
        else:
             print("   ❌ Error: DB pool should be open but is None")
             
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auto_connect())

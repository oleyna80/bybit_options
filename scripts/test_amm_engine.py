import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from bybit_options.services.amm.engine import AmmEngine

async def main():
    print("Testing AMM Engine Initialization...")
    engine = AmmEngine()
    try:
        await engine.initialize()
        print("✅ Engine Initialized.")
        
        # Test basic pricing
        from bybit_options.services.amm.pricing import OptionPricing
        price = OptionPricing.calculate_price(100000, 100000, 0.5, 0.05, 0.5, 'c')
        print(f"✅ Pricing Check: ATM Call (S=100k) ~ {price:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())

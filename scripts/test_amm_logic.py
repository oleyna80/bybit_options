import asyncio
import sys
import os
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from bybit_options.services.amm.engine import AmmEngine
from bybit_options.services.amm.models import AmmStrategy, AmmLeg, AmmOrder

# --- MOCKS ---

class MockRepo:
    async def get_active_strategies(self):
        leg1 = AmmLeg(symbol="BTC-26JUN26-100000-C", side="SELL", ratio=Decimal(1))
        # Note: In real app, ID is DB assigned. Here we mock it.
        leg1.id = 101
        
        strat = AmmStrategy(
            id=1,
            name="Test Strat",
            target_iv=Decimal("0.50"), 
            is_active=True,
            legs=[leg1]
        )
        return [strat]

    async def save_order(self, order):
        print(f"[MockDB] Saved Order: Price={order.price} Status={order.status}")
        return 5001 # Fake Order ID

    async def update_order_status(self, link_id, status):
        print(f"[MockDB] Update Order {link_id} -> {status}")

class MockMarketData:
    def __init__(self, testnet=False): pass
    async def start(self): pass
    def subscribe(self, syms): pass
    def get_market_iv(self, sym): return 0.45
    def get_mark_price(self, sym): return 5000.0
    async def stop(self): pass

class MockConnector:
    async def place_order(self, **kwargs):
        print(f"[MockConnector] PLACE ORDER: {kwargs}")
        return {"orderId": "Bybit_123", "orderLinkId": kwargs.get("orderLinkId")}
    
    async def amend_order(self, **kwargs):
        print(f"[MockConnector] AMEND ORDER: {kwargs}")
        return {}

# --- TEST ---

async def main():
    print("Testing AMM Logic + Execution Wiring...")
    
    engine = AmmEngine()
    engine.repo = MockRepo()
    engine.market_data = MockMarketData()
    engine.connector = MockConnector()
    
    # 1. Initialize
    engine.strategies = await engine.repo.get_active_strategies()
    print(f"Loaded {len(engine.strategies)} strategies.")
    
    # 2. Run Cycle 1 (Expect Place Order)
    print("\n--- Cycle 1: Logic -> Place ---")
    await engine.run_gardener_cycle()
    
    leg = engine.strategies[0].legs[0]
    if leg.active_order:
        print(f"✅ Success: Active Order created with LinkID: {leg.active_order.bybit_order_link_id}")
    else:
        print("❌ Failure: No Active Order set.")
        return

    # 3. Run Cycle 2 (Expect Ignore - Price Matches)
    print("\n--- Cycle 2: Logic -> Ignore (Stable Market) ---")
    await engine.run_gardener_cycle()
    
    # 4. Run Cycle 3 (Expect Amend - Price Shift)
    print("\n--- Cycle 3: Logic -> Amend (Market Moved) ---")
    # Hack: Shift target IV in strategy to force price change
    engine.strategies[0].target_iv = Decimal("0.60")
    await engine.run_gardener_cycle()
    
    print("\n✅ Test Execution Complete.")

if __name__ == "__main__":
    asyncio.run(main())

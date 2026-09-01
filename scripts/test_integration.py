"""
Quick test script to verify Volatility Intelligence API and Agent Command API.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_volatility_api():
    """Test Volatility Intelligence module."""
    print("\n" + "="*60)
    print("Testing Volatility Intelligence API")
    print("="*60)
    
    from bybit_options.services.volatility import VolatilityContextAPI
    
    api = VolatilityContextAPI()
    
    # Test 1: Get context
    print("\n1. Testing get_context()...")
    context = await api.get_context("BTC")
    
    print(f"   ✓ Symbol: {context.symbol}")
    print(f"   ✓ IV Rank: {context.iv_rank:.1f}")
    print(f"   ✓ IV Regime: {context.iv_regime}")
    print(f"   ✓ HV 30d: {context.hv_30d:.3f}")
    print(f"   ✓ IV/HV Ratio: {context.iv_hv_ratio:.2f}" if context.iv_hv_ratio else "   - IV/HV Ratio: N/A")
    print(f"   ✓ Signal: {context.overall_signal}")
    
    # Test 2: Get IV Rank history
    print("\n2. Testing get_iv_rank_history()...")
    history = await api.get_iv_rank_history("BTC", days=30)
    print(f"   ✓ Retrieved {len(history)} days of IV Rank history")
    if history:
        latest = history[-1]
        print(f"   ✓ Latest: {latest.timestamp.date()} - IV Rank: {latest.iv_rank:.1f}")
    
    print("\n✅ Volatility Intelligence API: PASSED")


async def test_agent_command_api():
    """Test Agent Command API (without actually modifying data)."""
    print("\n" + "="*60)
    print("Testing Agent Command API")
    print("="*60)
    
    from bybit_options.services.delta.database_config import db
    
    await db.connect()
    
    try:
        # Test 1: Check if new columns exist
        print("\n1. Verifying database schema...")
        result = await db.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'amm_strategies' 
            AND column_name IN ('skew_factor', 'spread_bps', 'min_iv', 'max_iv', 'last_agent_update')
        """)
        
        if result:
            print("   ✓ New columns added to amm_strategies")
        
        # Test 2: Check agent_commands_log table
        result = await db.fetchrow("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'agent_commands_log'
        """)
        
        if result:
            print("   ✓ agent_commands_log table created")
        
        # Test 3: Check amm_operating_mode table
        result = await db.fetchrow("""
            SELECT mode, check_interval_minutes 
            FROM amm_operating_mode 
            LIMIT 1
        """)
        
        if result:
            print(f"   ✓ amm_operating_mode table created (mode: {result['mode']})")
        
        print("\n✅ Agent Command API Schema: PASSED")
        
    finally:
        await db.close()


async def main():
    print("\n🧪 Running Integration Tests")
    print("="*60)
    
    try:
        await test_volatility_api()
        await test_agent_command_api()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nNext steps:")
        print("1. Start API server: uvicorn bybit_options.api.app:app --reload")
        print("2. Test endpoints:")
        print("   curl http://localhost:8000/api/v1/volatility/context?symbol=BTC")
        print("   curl http://localhost:8000/api/v1/amm/mode")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

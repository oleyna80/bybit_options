#!/usr/bin/env python3
"""
AMM Dashboard API Testing Script
=================================
Tests all AMM API endpoints to verify functionality.
"""

import asyncio
import httpx
from loguru import logger
import sys

BASE_URL = "http://localhost:8000/api/v1"


async def test_amm_endpoints():
    """Test all AMM Dashboard API endpoints."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "="*60)
        print("AMM Dashboard API Testing")
        print("="*60 + "\n")
        
        # Test 1: Get Strategies
        print("1️⃣  Testing GET /amm/strategies")
        try:
            response = await client.get(f"{BASE_URL}/amm/strategies")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {len(data.get('strategies', []))} strategies found")
                for strategy in data.get('strategies', []):
                    print(f"      - {strategy['name']} ({strategy['symbol']}) - {strategy['status']}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Get Portfolio Greeks
        print("\n2️⃣  Testing GET /amm/portfolio/greeks")
        try:
            response = await client.get(f"{BASE_URL}/amm/portfolio/greeks")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success:")
                print(f"      Delta: {data.get('delta', 0):.4f}")
                print(f"      Gamma: {data.get('gamma', 0):.2f}")
                print(f"      Vega:  {data.get('vega', 0):.2f}")
                print(f"      Theta: {data.get('theta', 0):.2f}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Get Risk Decisions
        print("\n3️⃣  Testing GET /amm/risk/decisions")
        try:
            response = await client.get(f"{BASE_URL}/amm/risk/decisions?limit=10")
            if response.status_code == 200:
                data = response.json()
                decisions = data.get('decisions', [])
                print(f"   ✅ Success: {len(decisions)} decisions found")
                for decision in decisions[:3]:
                    status = "✓ APPROVED" if decision['approved'] else "✗ REJECTED"
                    print(f"      - {decision['decision_type']}: {status} - {decision['reason']}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Get Engine Status
        print("\n4️⃣  Testing GET /amm/status")
        try:
            response = await client.get(f"{BASE_URL}/amm/status")
            if response.status_code == 200:
                data = response.json()
                status = "🟢 RUNNING" if data.get('is_running') else "🔴 STOPPED"
                print(f"   ✅ Success: Engine {status}")
                print(f"      Mode: {data.get('mode', 'UNKNOWN')}")
                if data.get('last_cycle_at'):
                    print(f"      Last Cycle: {data['last_cycle_at']}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 5: Get Operating Mode
        print("\n5️⃣  Testing GET /amm/mode")
        try:
            response = await client.get(f"{BASE_URL}/amm/mode")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: Mode = {data.get('mode', 'UNKNOWN')}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 6: Create Strategy (Test POST)
        print("\n6️⃣  Testing POST /amm/strategies (Create)")
        try:
            test_strategy = {
                "name": "Test Strategy (Auto-created)",
                "symbol": "BTC",
                "skew_factor": 1.0,
                "spread_bps": 15,
                "min_iv": 0.3,
                "max_iv": 1.5
            }
            response = await client.post(f"{BASE_URL}/amm/strategies", json=test_strategy)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: Created strategy ID {data.get('id')}")
                print(f"      Name: {data.get('name')}")
                print(f"      Status: {data.get('status')}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 7: Technical Context (Integration Test)
        print("\n7️⃣  Testing GET /technical/context (Integration)")
        try:
            response = await client.get(f"{BASE_URL}/technical/context?symbol=BTC")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success:")
                print(f"      Global Trend: {data.get('global_trend', 'UNKNOWN')}")
                print(f"      Signal: {data.get('trend_signal', 'UNKNOWN')}")
                print(f"      Confidence: {data.get('signal_confidence', 0):.2f}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 8: Volatility Context (Integration Test)
        print("\n8️⃣  Testing GET /volatility/context (Integration)")
        try:
            response = await client.get(f"{BASE_URL}/volatility/context?symbol=BTC")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success:")
                print(f"      IV Rank: {data.get('iv_rank', 0):.2f}")
                print(f"      IV Regime: {data.get('iv_regime', 'UNKNOWN')}")
                print(f"      Overall Signal: {data.get('signals', {}).get('overall', 'UNKNOWN')}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "="*60)
        print("✅ AMM Dashboard API Testing Complete")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Clean logging
    logger.remove()
    logger.add(sys.stderr, format="{message}")
    
    asyncio.run(test_amm_endpoints())

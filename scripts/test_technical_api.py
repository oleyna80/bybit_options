"""
Test script for Technical Intelligence API (TZ-TECH-001).

Validates:
1. GET /api/v1/technical/alligator
2. GET /api/v1/technical/fractals  
3. GET /api/v1/technical/context
"""

import asyncio
import httpx
from loguru import logger
import sys

BASE_URL = "http://localhost:8000/api/v1"


async def test_alligator_endpoint(client):
    """Test Alligator state endpoint."""
    logger.info("=== Testing Alligator Endpoint ===")
    
    for timeframe in ["W1", "D1", "H4", "H1"]:  # Test all supported timeframes
        try:
            response = await client.get(
                f"{BASE_URL}/technical/alligator",
                params={"symbol": "BTC", "timeframe": timeframe}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {timeframe} Alligator: state={data['state']}, "
                          f"spread={data['spread_pct']}%, direction={data['trend_direction']}")
            else:
                logger.error(f"❌ {timeframe} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ {timeframe} error: {e}")


async def test_fractals_endpoint(client):
    """Test fractals endpoint."""
    logger.info("\n=== Testing Fractals Endpoint ===")
    
    try:
        response = await client.get(
            f"{BASE_URL}/technical/fractals",
            params={"symbol": "BTC", "timeframe": "H4", "limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Found {data['count']} key fractals for H4")
            
            for fractal in data['fractals'][:3]:
                logger.info(f"   - {fractal['direction']}: ${fractal['price']:.0f} "
                          f"at {fractal['time'][:19]}")
        else:
            logger.error(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")


async def test_context_endpoint(client):
    """Test full technical context endpoint."""
    logger.info("\n=== Testing Technical Context Endpoint ===")
    
    try:
        response = await client.get(
            f"{BASE_URL}/technical/context",
            params={"symbol": "BTC"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            logger.info(f"✅ Technical Context Retrieved:")
            logger.info(f"   Current Price: ${data['current_price']:.2f}")
            logger.info(f"   Global Trend: {data['global_trend']}")
            logger.info(f"   Signal: {data['trend_signal']} (confidence: {data['signal_confidence']})")
            
            # Alligator states
            logger.info("\n   Alligator States:")
            for tf in ["W1", "D1", "H4"]:
                alg = data['alligator'].get(tf)
                if alg:
                    logger.info(f"     {tf}: {alg['state']} (spread: {alg['spread_pct']}%)")
                else:
                    logger.info(f"     {tf}: No data")
            
            # Levels
            logger.info("\n   Key Levels:")
            res = data['levels']['nearest_resistance']
            sup = data['levels']['nearest_support']
            
            if res:
                logger.info(f"     Resistance: ${res['price']:.0f} ({res['timeframe']}, +{res['distance_pct']:.1f}%)")
            else:
                logger.info(f"     Resistance: None")
                
            if sup:
                logger.info(f"     Support: ${sup['price']:.0f} ({sup['timeframe']}, -{sup['distance_pct']:.1f}%)")
            else:
                logger.info(f"     Support: None")
                
            return data
            
        else:
            logger.error(f"❌ Failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_integration_with_volatility(client):
    """Test integration: Technical + Volatility contexts."""
    logger.info("\n=== Testing Technical + Volatility Integration ===")
    
    try:
        # Get both contexts
        tech_resp = await client.get(f"{BASE_URL}/technical/context?symbol=BTC")
        vol_resp = await client.get(f"{BASE_URL}/volatility/context?symbol=BTC")
        
        if tech_resp.status_code == 200 and vol_resp.status_code == 200:
            tech = tech_resp.json()
            vol = vol_resp.json()
            
            logger.info("✅ Both contexts available")
            logger.info(f"\n   Combined Analysis:")
            logger.info(f"   - Trend Signal: {tech['trend_signal']}")
            logger.info(f"   - IV Rank: {vol['iv_rank']:.2f}")
            logger.info(f"   - IV Regime: {vol['iv_regime']}")
            logger.info(f"   - Overall Vol Signal: {vol['signals']['overall']}")
            
            # Decision logic example
            logger.info(f"\n   Recommended Strategy:")
            
            if tech['trend_signal'] == 'BUY_DELTA' and vol['iv_regime'] == 'LOW':
                logger.info("     → BUY CALLS (trend + cheap premium)")
            elif tech['trend_signal'] == 'SELL_DELTA' and vol['iv_regime'] == 'LOW':
                logger.info("     → BUY PUTS (trend + cheap premium)")
            elif tech['trend_signal'] == 'NEUTRAL' and vol['iv_regime'] == 'HIGH':
                logger.info("     → SELL STRADDLE/STRANGLE (no trend + expensive premium)")
            elif tech['global_trend'] == 'BULLISH' and vol['iv_regime'] == 'HIGH':
                logger.info("     → ADJUST AMM SKEW (favor call selling in uptrend)")
            else:
                logger.info("     → WAIT / DELTA-NEUTRAL")
                
        else:
            logger.error("❌ Failed to get one or both contexts")
            
    except Exception as e:
        logger.error(f"❌ Integration test error: {e}")


async def main():
    """Run all tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check if server is running
            health_resp = await client.get(f"{BASE_URL}/../health", timeout=5.0)
            logger.info("✅ API server is running\n")
        except Exception:
            logger.error("❌ API server not running at http://localhost:8000")
            logger.error("   Start server with: python -m bybit_options.api.app")
            return
        
        # Run tests
        await test_alligator_endpoint(client)
        await test_fractals_endpoint(client)
        context = await test_context_endpoint(client)
        
        if context:
            await test_integration_with_volatility(client)
        
        logger.info("\n" + "="*60)
        logger.info("✅ ALL TESTS COMPLETED")
        logger.info("="*60)


if __name__ == "__main__":
    # Clean logging
    logger.remove()
    logger.add(sys.stderr, format="{message}")
    
    asyncio.run(main())

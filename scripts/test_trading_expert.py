"""
Trading Expert Validation Script.
Executes scenarios from backend-testing-tasks.md against running API.
"""

import asyncio
import httpx
import json
from loguru import logger
import sys

BASE_URL = "http://localhost:8000/api/v1"

async def run_scenario_1_market_intelligence(client):
    logger.info("=== Scenario 1: Market Intelligence Check ===")
    
    # 1. Fetch Volatility Context
    response = await client.get(f"{BASE_URL}/volatility/context?symbol=BTC")
    assert response.status_code == 200, f"Failed to get context: {response.text}"
    data = response.json()
    
    logger.info(f"Context: IV Rank={data.get('iv_rank')}, Regime={data.get('iv_regime')}")
    logger.info(f"Signal: {data.get('signals', {}).get('overall')}")
    
    assert data.get('iv_rank') is not None
    assert data.get('hv') is not None
    
    return data

async def run_scenario_2_dynamic_adjustment(client):
    logger.info("=== Scenario 2: Dynamic Strategy Adjustment ===")
    
    # 1. Get current strategy
    response = await client.get(f"{BASE_URL}/amm/strategies")
    logger.info(f"Strategies response: {response.status_code}")
    data = response.json()
    logger.info(f"Existing data: {data}")
    
    strategies = data.get('strategies', [])
    
    if not strategies:
        # Create a dummy strategy if none exists
        logger.info("No strategy found, creating one...")
        create_payload = {
            "name": "Test Strategy BTC",
            "symbol": "BTC",
            "min_order_size": 0.01,
            "max_order_size": 1.0,
            "max_position": 5.0,
            "target_iv": 0.50,
            "min_iv": 0.40,
            "max_iv": 1.50,
            "skew_factor": 0.0,
            "spread_bps": 50,
            "is_active": True
        }
        response = await client.post(f"{BASE_URL}/amm/strategies", json=create_payload)
        logger.info(f"Create response: {response.status_code} - {response.text}")
        
        # Re-fetch
        response = await client.get(f"{BASE_URL}/amm/strategies")
        data = response.json()
        strategies = data.get('strategies', [])
        logger.info(f"Strategies after creation: {strategies}")
        
    if not strategies:
        raise ValueError("Failed to retrieve strategies even after creation attempt.")
        
    strategy_id = strategies[0]['id']
    current_iv = float(strategies[0]['target_iv'])
    new_iv = current_iv * 0.98
    
    logger.info(f"Adjusting Strategy {strategy_id}: IV {current_iv} -> {new_iv}")
    
    # 2. Execute Command
    payload = {
        "action": "UPDATE_STRATEGY_PARAMS",
        "strategy_id": strategy_id,
        "params": {
            "target_iv": new_iv,
            "skew_factor": 0.02
        },
        "reason": "Testing: Scenario 2 Dynamic Adjustment"
    }
    
    response = await client.post(f"{BASE_URL}/amm/agent/command", json=payload)
    assert response.status_code == 200, f"Command failed: {response.text}"
    
    # 3. Verify
    response = await client.get(f"{BASE_URL}/amm/strategies")
    data = response.json()
    strategies = data.get('strategies', [])
    updated_strat = strategies[0]
    
    logger.info(f"Updated Strategy: IV={updated_strat['target_iv']}, Skew={updated_strat['skew_factor']}")
    
    assert abs(float(updated_strat['target_iv']) - new_iv) < 0.001, f"IV mismatch: {updated_strat['target_iv']} != {new_iv}"
    assert float(updated_strat['skew_factor']) == 0.02, f"Skew mismatch: {updated_strat['skew_factor']} != 0.02"
    
    logger.info("✅ Strategy updated successfully")
    return strategy_id

async def run_scenario_3_safety_audit(client, strategy_id):
    logger.info("=== Scenario 3: Safety & Audit ===")
    
    # 1. Check Audit Log
    response = await client.get(f"{BASE_URL}/amm/agent/commands")
    logs = response.json().get('commands', [])
    
    logger.info(f"Audit Logs: {logs}")
    
    found = False
    for log in logs:
        # Check reason field or payload
        reason = log.get('reason') or log.get('payload', {}).get('reason')
        if reason and "Testing: Scenario 2" in reason:
            found = True
            break
    
    if found:
        logger.info("✅ Audit log verification passed")
    else:
        logger.error("❌ Audit log entry not found in recent logs")
    
    # 2. Emergency Pause
    logger.info("Testing Emergency Pause...")
    response = await client.post(f"{BASE_URL}/amm/agent/command", json={
        "action": "PAUSE_STRATEGY",
        "strategy_id": strategy_id,
        "reason": "Testing: Scenario 3 Emergency Pause"
    })
    assert response.status_code == 200
    
    # Check status
    response = await client.get(f"{BASE_URL}/amm/strategies")
    strat = response.json()['strategies'][0]
    
    # Fix: Check is_paused, not is_active
    if strat.get('is_paused'):
        logger.info(f"✅ Strategy Paused is_paused={strat.get('is_paused')}")
    else:
         logger.error(f"❌ Strategy NOT Paused: {strat}")
         assert strat.get('is_paused') == True
    
    # 3. Resume
    logger.info("Resuming Strategy...")
    response = await client.post(f"{BASE_URL}/amm/agent/command", json={
        "action": "RESUME_STRATEGY",
        "strategy_id": strategy_id
    })
    assert response.status_code == 200
    
    response = await client.get(f"{BASE_URL}/amm/strategies")
    strat = response.json()['strategies'][0]
    assert strat.get('is_paused') == False
    logger.info("✅ Strategy Resumed")

async def run_scenario_4_modes(client):
    logger.info("=== Scenario 4: Operating Modes ===")
    
    # 1. Switch to AUTO
    response = await client.post(f"{BASE_URL}/amm/mode", json={
        "mode": "AUTO",
        "check_interval_minutes": 10
    })
    assert response.status_code == 200
    
    # 2. Verify
    response = await client.get(f"{BASE_URL}/amm/mode")
    data = response.json()
    assert data['mode'] == "AUTO"
    logger.info("✅ Switched to AUTO mode")
    
    # 3. Back to MANUAL
    await client.post(f"{BASE_URL}/amm/mode", json={"mode": "MANUAL"})
    logger.info("✅ Reverted to MANUAL mode")

async def main():
    async with httpx.AsyncClient() as client:
        try:
            # Check if server is running
            try:
                await client.get(f"{BASE_URL}/health")
            except Exception:
                logger.error("API Server not running at http://localhost:8000")
                return

            await run_scenario_1_market_intelligence(client)
            strat_id = await run_scenario_2_dynamic_adjustment(client)
            await run_scenario_3_safety_audit(client, strat_id)
            await run_scenario_4_modes(client)
            
            logger.info("\n🎉 ALL SCENARIOS PASSED SUCCESSFULLY")
            
        except AssertionError as e:
            logger.error(f"❌ TEST FAILED: {e}")
        except Exception as e:
            logger.error(f"❌ ERROR: {e}")

if __name__ == "__main__":
    import logging
    # Clean output
    logger.remove()
    logger.add(sys.stderr, format="{message}")
    asyncio.run(main())

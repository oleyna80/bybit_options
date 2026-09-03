#!/usr/bin/env python3
"""
Test script for Bybit options IV testing.
This script creates and executes test_iv.py to test Bybit API connectivity.
"""

import os
import subprocess
import sys
import tempfile

def create_test_iv_script():
    """Create the test_iv.py script content."""
    return '''import asyncio
from bybit_options.services.bybit_connector import BybitConnector
from config import get_config

async def test():
    config = get_config()
    connector = BybitConnector(config.bybit.api_key, config.bybit.api_secret, testnet=False)
    
    # Инициализировать сессию
    await connector._init_session()
    
    # Запрос с правильным параметром
    result = await connector.get_tickers(category='option', base_coin='BTC')
    
    if result:
        first = result[0]
        print(f"Symbol: {first.get('symbol')}")
        print(f"markIv: {first.get('markIv')}")
        print(f"bidIv: {first.get('bidIv')}")
        print(f"askIv: {first.get('askIv')}")
        print(f"\\nTotal options: {len(result)}")
    else:
        print("No tickers returned")
    
    await connector.close()

if __name__ == "__main__":
    asyncio.run(test())
'''

def main():
    """Main function to create and execute test script."""
    print("Creating test_iv.py...")
    
    # Create the test script
    script_content = create_test_iv_script()
    
    # Write to file
    with open('test_iv.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("Created test_iv.py")
    print("Running test_iv.py...")
    
    # Execute the script
    try:
        result = subprocess.run(
            [sys.executable, 'test_iv.py'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        print("Test completed successfully")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Test failed with exit code {e.returncode}")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        return 1
    except FileNotFoundError:
        print("Error: Python interpreter not found")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
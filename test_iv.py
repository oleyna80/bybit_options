import asyncio
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
        print(f"\nTotal options: {len(result)}")
    else:
        print("No tickers returned")
    
    await connector.close()

asyncio.run(test())

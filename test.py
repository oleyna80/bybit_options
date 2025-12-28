from pybit.unified_trading import HTTP
session = HTTP(testnet=False)

# Проверить market data для конкретного опциона
response = session.get_tickers(
    category="option",
    symbol="BTC-30JAN26-78000-P-USDT"  # актуальный тикер из твоих позиций
)

print("\n=== MARKET DATA ===")
if response['result']['list']:
    ticker = response['result']['list'][0]
    print(f"Symbol: {ticker['symbol']}")
    print(f"Mark Price: {ticker.get('markPrice')}")
    print(f"Mark IV: {ticker.get('markIv')}")
    print(f"Delta: {ticker.get('delta')}")
    print(f"Vega: {ticker.get('vega')}")
    print(f"Gamma: {ticker.get('gamma')}")
    print(f"Theta: {ticker.get('theta')}")
    print(f"Bid: {ticker.get('bid1Price')}")
    print(f"Ask: {ticker.get('ask1Price')}")
    print("\nAll available fields:", ticker.keys())
else:
    print("No data - try another symbol")
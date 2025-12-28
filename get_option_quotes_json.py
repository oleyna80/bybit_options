"""
Option Quotes Fetcher - JSON Output
Get current market data for specific BTC options in JSON format

Usage:
    python get_option_quotes_json.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C
    python get_option_quotes_json.py --symbols BTC-19DEC25-82000-P,BTC-19DEC25-89000-C
    python get_option_quotes_json.py BTC-19DEC25-82000-P > quotes.json
"""
import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from bybit_connector import BybitConnector


async def get_option_quotes_json(symbols: list):
    """
    Fetch current option quotes from Bybit API and return as JSON
    
    Args:
        symbols: List of option symbols (e.g., 'BTC-19DEC25-82000-P')
    """
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print(json.dumps({
            "success": False,
            "error": "BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env"
        }, indent=2))
        sys.exit(1)
    
    # Convert to full symbols with -USDT suffix if needed
    full_symbols = []
    for sym in symbols:
        if not sym.endswith("-USDT"):
            sym = f"{sym}-USDT"
        full_symbols.append(sym)
    
    async with BybitConnector(api_key, api_secret, testnet=False) as conn:
        # Fetch all quotes in parallel
        tasks = [
            conn.get_tickers(category="option", symbol=symbol)
            for symbol in full_symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        quotes = []
        
        for symbol, result in zip(full_symbols, results):
            if isinstance(result, Exception):
                quotes.append({
                    "symbol": symbol,
                    "error": str(result)
                })
                continue
            
            if not result:
                quotes.append({
                    "symbol": symbol,
                    "error": "No data"
                })
                continue
            
            ticker = result[0]
            
            # Extract data
            bid_price = float(ticker.get("bid1Price", 0))
            ask_price = float(ticker.get("ask1Price", 0))
            mark_price = float(ticker.get("markPrice", 0))
            last_price = float(ticker.get("lastPrice", 0))
            
            bid_iv = float(ticker.get("bid1Iv", 0))
            ask_iv = float(ticker.get("ask1Iv", 0))
            mark_iv = float(ticker.get("markIv", 0))
            
            delta = float(ticker.get("delta", 0))
            gamma = float(ticker.get("gamma", 0))
            vega = float(ticker.get("vega", 0))
            theta = float(ticker.get("theta", 0))
            
            open_interest = float(ticker.get("openInterest", 0))
            underlying_price = float(ticker.get("underlyingPrice", 0))
            bid_size = float(ticker.get("bid1Size", 0))
            ask_size = float(ticker.get("ask1Size", 0))
            volume_24h = float(ticker.get("volume24h", 0))
            turnover_24h = float(ticker.get("turnover24h", 0))
            
            # Calculate spread
            spread_abs = ask_price - bid_price if ask_price > 0 and bid_price > 0 else 0
            spread_pct = (spread_abs / mark_price * 100) if mark_price > 0 else 0
            
            quotes.append({
                "symbol": symbol,
                "prices": {
                    "mark": round(mark_price, 2),
                    "bid": round(bid_price, 2),
                    "ask": round(ask_price, 2),
                    "last": round(last_price, 2),
                    "underlying_btc": round(underlying_price, 2)
                },
                "spread": {
                    "absolute": round(spread_abs, 2),
                    "percent": round(spread_pct, 4)
                },
                "iv": {
                    "bid": round(bid_iv, 6),
                    "mark": round(mark_iv, 6),
                    "ask": round(ask_iv, 6)
                },
                "greeks": {
                    "delta": round(delta, 6),
                    "gamma": round(gamma, 8),
                    "vega": round(vega, 2),
                    "theta": round(theta, 2)
                },
                "liquidity": {
                    "bid_size": round(bid_size, 2),
                    "ask_size": round(ask_size, 2),
                    "open_interest": round(open_interest, 2),
                    "volume_24h": round(volume_24h, 2),
                    "turnover_24h": round(turnover_24h, 0)
                }
            })
        
        # Return JSON response
        response = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "count": len(quotes),
            "quotes": quotes
        }
        
        return response


def main():
    """Parse arguments and fetch quotes"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("Example:")
        print("  python get_option_quotes_json.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C")
        sys.exit(1)
    
    symbols = sys.argv[1:]
    
    # Validate symbols
    for symbol in symbols:
        if not symbol.startswith("BTC-") or not any(x in symbol for x in ["C", "P"]):
            print(f"❌ Invalid symbol format: {symbol}")
            print("Expected format: BTC-DDMMMYY-STRIKE-TYPE (e.g., BTC-19DEC25-82000-P)")
            sys.exit(1)
    
    result = asyncio.run(get_option_quotes_json(symbols))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

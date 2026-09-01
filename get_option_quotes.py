"""
Quick Option Quotes Fetcher
Get current market data for specific BTC options for trading decisions

Usage:
    python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C
    python get_option_quotes.py BTC-19DEC25-82000-P  # single option
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from bybit_options.services.bybit_connector import BybitConnector


async def get_option_quotes(symbols: list):
    """
    Fetch current option quotes from Bybit API
    
    Args:
        symbols: List of option symbols (e.g., 'BTC-19DEC25-82000-P')
    """
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env")
        sys.exit(1)
    
    # Convert to full symbols with -USDT suffix if needed
    full_symbols = []
    for sym in symbols:
        if not sym.endswith("-USDT"):
            sym = f"{sym}-USDT"
        full_symbols.append(sym)
    
    print(f"\n{'='*100}")
    print(f"📊 BTC OPTIONS MARKET QUOTES")
    print(f"{'='*100}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    async with BybitConnector(api_key, api_secret, testnet=False) as conn:
        # Fetch all quotes in parallel
        tasks = [
            conn.get_tickers(category="option", symbol=symbol)
            for symbol in full_symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        quotes_data = []
        
        for symbol, result in zip(full_symbols, results):
            if isinstance(result, Exception):
                print(f"❌ Error fetching {symbol}: {result}")
                continue
            
            if not result:
                print(f"⚠️  No data for {symbol}")
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
            
            # Calculate spread
            spread_abs = ask_price - bid_price if ask_price > 0 and bid_price > 0 else 0
            spread_pct = (spread_abs / mark_price * 100) if mark_price > 0 else 0
            
            # Parse symbol for better display
            symbol_parts = symbol.replace("-USDT", "").split("-")
            strike = symbol_parts[2] if len(symbol_parts) > 2 else "?"
            option_type = symbol_parts[3] if len(symbol_parts) > 3 else "?"
            expiry = symbol_parts[1] if len(symbol_parts) > 1 else "?"
            
            option_label = f"{option_type} ${strike}"
            
            quotes_data.append({
                "Option": option_label,
                "Expiry": expiry,
                "Mark": f"${mark_price:.2f}",
                "Bid": f"${bid_price:.2f}",
                "Ask": f"${ask_price:.2f}",
                "Spread": f"${spread_abs:.2f} ({spread_pct:.2f}%)",
                "IV": f"{mark_iv:.2%}",
                "Delta": f"{delta:+.4f}",
                "Gamma": f"{gamma:.6f}",
                "Vega": f"{vega:+.2f}",
                "Theta": f"{theta:+.2f}",
                "OI": f"{open_interest:.2f}",
                "Last": f"${last_price:.2f}",
            })
        
        # Display table
        if quotes_data:
            # Print header
            print("\n" + "="*180)
            header_row = "| " + " | ".join([f"{h:^20}" for h in quotes_data[0].keys()]) + " |"
            print(header_row)
            print("="*180)
            
            # Print data rows
            for row in quotes_data:
                data_row = "| " + " | ".join([f"{str(v):^20}" for v in row.values()]) + " |"
                print(data_row)
            
            print("="*180 + "\n")
            
            # Additional details
            print(f"\n{'='*100}")
            print("📌 DETAILS\n")
            
            for i, (symbol, result) in enumerate(zip(full_symbols, results)):
                if isinstance(result, Exception) or not result:
                    continue
                
                ticker = result[0]
                bid_price = float(ticker.get("bid1Price", 0))
                ask_price = float(ticker.get("ask1Price", 0))
                bid_iv = float(ticker.get("bid1Iv", 0))
                ask_iv = float(ticker.get("ask1Iv", 0))
                mark_iv = float(ticker.get("markIv", 0))
                underlying_price = float(ticker.get("underlyingPrice", 0))
                
                print(f"{symbol}")
                print(f"  Underlying (BTC): ${underlying_price:,.2f}")
                print(f"  Bid IV: {bid_iv:.2%} | Mark IV: {mark_iv:.2%} | Ask IV: {ask_iv:.2%}")
                print(f"  Bid Size: {float(ticker.get('bid1Size', 0)):.2f} | Ask Size: {float(ticker.get('ask1Size', 0)):.2f}")
                print(f"  24h Volume: {float(ticker.get('volume24h', 0)):.2f} | 24h Turnover: ${float(ticker.get('turnover24h', 0)):,.0f}")
                print()
            
            print(f"{'='*100}\n")
        else:
            print("❌ No quotes received")


def main():
    """Parse arguments and fetch quotes"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("Example:")
        print("  python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C")
        sys.exit(1)
    
    symbols = sys.argv[1:]
    
    # Validate symbols
    for symbol in symbols:
        if not symbol.startswith("BTC-") or not any(x in symbol for x in ["C", "P"]):
            print(f"❌ Invalid symbol format: {symbol}")
            print("Expected format: BTC-DDMMMYY-STRIKE-TYPE (e.g., BTC-19DEC25-82000-P)")
            sys.exit(1)
    
    asyncio.run(get_option_quotes(symbols))


if __name__ == "__main__":
    main()

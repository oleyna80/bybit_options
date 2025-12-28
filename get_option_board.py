"""
Option Board Fetcher - Table Format
Get complete option board for BTC-2JAN26 with strikes 75000-110000

Usage:
    python get_option_board.py
    python get_option_board.py --type call
    python get_option_board.py --type put
    python get_option_board.py --min-strike 80000 --max-strike 90000
    python get_option_board.py --save option_board.md
"""

import asyncio
import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bybit_connector import BybitConnector
from option_board_utils import (
    generate_option_symbols,
    parse_option_symbol,
    format_option_display,
    calculate_board_statistics,
    sort_options_for_display,
    get_all_option_series,
    fetch_option_tickers
)


async def fetch_option_board(
    connector: BybitConnector,
    symbols: List[str],
    batch_size: int = 20
) -> Dict[str, Any]:
    """
    Fetch option data for a list of symbols in batches
    
    Args:
        connector: BybitConnector instance
        symbols: List of option symbols
        batch_size: Number of symbols to fetch in parallel
    
    Returns:
        Dictionary with option data and statistics
    """
    all_options = []
    successful_symbols = []
    failed_symbols = []
    
    # Get underlying BTC price
    btc_tickers = await connector.get_tickers(category="spot", symbol="BTCUSDT")
    underlying_price = 0
    if btc_tickers and len(btc_tickers) > 0:
        underlying_price = float(btc_tickers[0].get("lastPrice", 0))
    
    # Process symbols in batches to avoid rate limiting
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        
        # Fetch all tickers in parallel - need to add -USDT suffix for API
        tasks = [
            connector.get_tickers(category="option", symbol=f"{symbol}-USDT")
            for symbol in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for symbol, result in zip(batch, results):
            if isinstance(result, Exception):
                failed_symbols.append({
                    "symbol": symbol,
                    "error": str(result)
                })
                continue
            
            if not result:
                failed_symbols.append({
                    "symbol": symbol,
                    "error": "No data returned"
                })
                continue
            
            ticker = result[0]
            
            # Parse symbol and format data
            try:
                symbol_data = parse_option_symbol(symbol)
                option_data = format_option_display(symbol_data, ticker, underlying_price)
                all_options.append(option_data)
                successful_symbols.append(symbol)
            except Exception as e:
                failed_symbols.append({
                    "symbol": symbol,
                    "error": f"Processing error: {str(e)}"
                })
    
    # Calculate statistics
    statistics = calculate_board_statistics(all_options)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "underlying_price": underlying_price,
        "successful_count": len(successful_symbols),
        "failed_count": len(failed_symbols),
        "options": all_options,
        "statistics": statistics,
        "failed_symbols": failed_symbols
    }


def print_option_board_table(options_data: List[Dict[str, Any]], board_data: Dict[str, Any], base_coin: str, expiry: str):
    """
    Print option board in formatted table
    
    Args:
        options_data: List of formatted option data
        board_data: Complete board data with statistics
        base_coin: Base coin (BTC, ETH, etc)
        expiry: Expiry date (e.g., 2JAN26)
    """
    # Header
    print("\n" + "="*180)
    print(f"{base_coin}-{expiry} OPTION BOARD")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Underlying {base_coin} Price: ${board_data['underlying_price']:,.2f}")
    print(f"Options: {board_data['successful_count']} successful, {board_data['failed_count']} failed")
    print("="*180)
    
    # Table header
    header = [
        "STRIKE", "TYPE", "MONEY", "MARK", "BID/ASK", "SPREAD%",
        "IV%", "DELTA", "GAMMA", "VEGA", "THETA", "OI"
    ]
    
    header_row = "| " + " | ".join([f"{h:^10}" for h in header]) + " |"
    separator = "|" + "|".join(["-"*12 for _ in header]) + "|"
    
    print(separator)
    print(header_row)
    print(separator)
    
    # Table rows
    for option in options_data:
        # Color coding for moneyness
        moneyness = option["moneyness"]
        moneyness_display = moneyness
        
        # Format prices
        mark_price = f"${option['prices']['mark']:,.0f}" if option['prices']['mark'] >= 100 else f"${option['prices']['mark']:,.2f}"
        bid_ask = f"${option['prices']['bid']:,.0f}/${option['prices']['ask']:,.0f}"
        
        # Format Greeks
        delta = f"{option['greeks']['delta']:+.4f}"
        gamma = f"{option['greeks']['gamma']:.5f}"
        vega = f"{option['greeks']['vega']:,.0f}"
        theta = f"{option['greeks']['theta']:,.0f}"
        
        # Format other values
        spread_pct = f"{option['spread']['percent']:.2f}%"
        iv_pct = f"{option['iv']['mark']*100:.1f}%"
        oi = f"{option['liquidity']['open_interest']:,.0f}"
        
        row_data = [
            f"{option['strike']:>10,}",
            f"{option['type'].upper():^10}",
            f"{moneyness_display:^10}",
            f"{mark_price:>10}",
            f"{bid_ask:>10}",
            f"{spread_pct:>10}",
            f"{iv_pct:>10}",
            f"{delta:>10}",
            f"{gamma:>10}",
            f"{vega:>10}",
            f"{theta:>10}",
            f"{oi:>10}"
        ]
        
        row = "| " + " | ".join(row_data) + " |"
        print(row)
    
    print(separator)
    
    # Statistics
    stats = board_data["statistics"]
    if stats:
        print(f"\nBOARD STATISTICS:")
        print(f"   Total Options: {stats['total_options']} (Calls: {stats['calls_count']}, Puts: {stats['puts_count']})")
        print(f"   Moneyness: ITM={stats['moneyness_distribution'].get('ITM', 0)}, "
              f"ATM={stats['moneyness_distribution'].get('ATM', 0)}, "
              f"OTM={stats['moneyness_distribution'].get('OTM', 0)}")
        print(f"   Average Spread: {stats['averages']['spread_percent']:.2f}%")
        print(f"   Average IV: {stats['averages']['iv']*100:.2f}%")
        
        if stats['most_liquid']['by_open_interest']:
            print(f"   Most Liquid (OI): {stats['most_liquid']['by_open_interest']}")
        if stats['most_liquid']['by_volume']:
            print(f"   Most Active (Volume): {stats['most_liquid']['by_volume']}")


def save_to_markdown(options_data: List[Dict[str, Any]], board_data: Dict[str, Any], filename: str, base_coin: str, expiry: str):
    """
    Save option board to markdown file
    
    Args:
        options_data: List of formatted option data
        board_data: Complete board data
        filename: Output filename
        base_coin: Base coin (BTC, ETH, etc)
        expiry: Expiry date (e.g., 2JAN26)
    """
    with open(filename, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"# {base_coin}-{expiry} Option Board\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"**Underlying {base_coin} Price**: ${board_data['underlying_price']:,.2f}\n")
        f.write(f"**Options**: {board_data['successful_count']} successful, {board_data['failed_count']} failed\n\n")
        
        # Statistics
        stats = board_data["statistics"]
        if stats:
            f.write("## Board Statistics\n\n")
            f.write(f"- **Total Options**: {stats['total_options']}\n")
            f.write(f"- **Calls**: {stats['calls_count']}\n")
            f.write(f"- **Puts**: {stats['puts_count']}\n")
            f.write(f"- **ITM/ATM/OTM**: {stats['moneyness_distribution'].get('ITM', 0)}/{stats['moneyness_distribution'].get('ATM', 0)}/{stats['moneyness_distribution'].get('OTM', 0)}\n")
            f.write(f"- **Average Spread**: {stats['averages']['spread_percent']:.2f}%\n")
            f.write(f"- **Average IV**: {stats['averages']['iv']*100:.2f}%\n\n")
        
        # Options table
        f.write("## Option Data\n\n")
        f.write("| Strike | Type | Moneyness | Mark Price | Bid/Ask | Spread % | IV % | Delta | Gamma | Vega | Theta | OI |\n")
        f.write("|--------|------|-----------|------------|---------|----------|------|-------|-------|------|-------|----|\n")
        
        for option in options_data:
            mark_price = f"${option['prices']['mark']:,.0f}" if option['prices']['mark'] >= 100 else f"${option['prices']['mark']:,.2f}"
            bid_ask = f"${option['prices']['bid']:,.0f}/${option['prices']['ask']:,.0f}"
            
            row = (
                f"| {option['strike']:,} | "
                f"{option['type'].upper()} | "
                f"{option['moneyness']} | "
                f"{mark_price} | "
                f"{bid_ask} | "
                f"{option['spread']['percent']:.2f}% | "
                f"{option['iv']['mark']*100:.1f}% | "
                f"{option['greeks']['delta']:+.4f} | "
                f"{option['greeks']['gamma']:.5f} | "
                f"{option['greeks']['vega']:,.0f} | "
                f"{option['greeks']['theta']:,.0f} | "
                f"{option['liquidity']['open_interest']:,.0f} |"
            )
            f.write(row + "\n")
        
        # Failed symbols (if any)
        if board_data['failed_symbols']:
            f.write("\n## Failed Symbols\n\n")
            for failed in board_data['failed_symbols']:
                f.write(f"- `{failed['symbol']}`: {failed['error']}\n")
        
        print(f"[SAVED] Report saved to: {filename}")


async def get_real_option_symbols(connector, base_coin="BTC", expiry=None, option_type=None):
    """
    Get real option symbols from Bybit API
    
    Args:
        connector: BybitConnector instance
        base_coin: Base coin (BTC, ETH, etc)
        expiry: Expiry date (e.g., "2JAN26") or None for all expiries
        option_type: "C" for call, "P" for put, or None for both
    
    Returns:
        List of option symbols (without -USDT suffix)
    """
    # Get all instruments
    instruments = await connector.get_instruments_info(
        category="option",
        base_coin=base_coin
    )
    
    symbols = []
    for instrument in instruments:
        symbol = instrument.get("symbol", "")
        if not symbol or "-USDT" not in symbol:
            continue
        
        # Remove -USDT suffix
        clean_symbol = symbol.replace("-USDT", "")
        
        # Parse symbol to check expiry and type
        try:
            parsed = parse_option_symbol(clean_symbol)
            
            # Filter by expiry if specified
            if expiry and parsed["expiry"] != expiry:
                continue
            
            # Filter by option type if specified
            if option_type and parsed["option_type"] != option_type:
                continue
            
            symbols.append(clean_symbol)
        except Exception:
            continue
    
    return symbols


async def main():
    """Main execution function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Fetch real option board from Bybit")
    parser.add_argument("--base-coin", type=str, default="BTC",
                       help="Base coin (BTC, ETH, etc) (default: BTC)")
    parser.add_argument("--expiry", type=str, default=None,
                       help="Expiry date (e.g., 2JAN26). If not specified, uses first available expiry")
    parser.add_argument("--type", choices=["all", "call", "put"], default="all",
                       help="Option type to fetch (default: all)")
    parser.add_argument("--min-strike", type=int, default=None,
                       help="Minimum strike price (optional filter)")
    parser.add_argument("--max-strike", type=int, default=None,
                       help="Maximum strike price (optional filter)")
    parser.add_argument("--limit", type=int, default=50,
                       help="Maximum number of options to fetch (default: 50)")
    parser.add_argument("--save", type=str,
                       help="Save output to markdown file")
    parser.add_argument("--sort-by", choices=["strike", "mark_price", "delta", "iv", "spread"],
                       default="strike", help="Sort options by field")
    parser.add_argument("--sort-order", choices=["asc", "desc"], default="asc",
                       help="Sort order")
    
    args = parser.parse_args()
    
    # Determine option types
    if args.type == "call":
        option_type_code = "C"
    elif args.type == "put":
        option_type_code = "P"
    else:
        option_type_code = None
    
    print(f"[INFO] Fetching real option data from Bybit...")
    print(f"   Base coin: {args.base_coin}")
    print(f"   Option type: {args.type}")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env")
        sys.exit(1)
    
    # Fetch data
    try:
        async with BybitConnector(api_key, api_secret, testnet=False) as connector:
            # Get available series
            all_series = await get_all_option_series(connector, args.base_coin)
            if not all_series:
                print("❌ ERROR: No option series found for this base coin")
                sys.exit(1)
            
            # Determine expiry to use
            selected_expiry = args.expiry
            if not selected_expiry:
                selected_expiry = all_series[0]
                print(f"   Using first available expiry: {selected_expiry}")
            else:
                if selected_expiry not in all_series:
                    print(f"❌ ERROR: Expiry {selected_expiry} not found. Available series: {all_series}")
                    sys.exit(1)
            
            print(f"   Expiry: {selected_expiry}")
            print(f"   Available series: {all_series}")
            
            # Get real option symbols
            symbols = await get_real_option_symbols(
                connector,
                base_coin=args.base_coin,
                expiry=selected_expiry,
                option_type=option_type_code
            )
            
            if not symbols:
                print("❌ ERROR: No option symbols found with the specified filters")
                sys.exit(1)
            
            # Apply strike filters if specified
            filtered_symbols = []
            for symbol in symbols:
                try:
                    parsed = parse_option_symbol(symbol)
                    strike = parsed["strike"]
                    
                    if args.min_strike is not None and strike < args.min_strike:
                        continue
                    if args.max_strike is not None and strike > args.max_strike:
                        continue
                    
                    filtered_symbols.append(symbol)
                except Exception:
                    continue
            
            symbols = filtered_symbols
            
            # Limit number of symbols
            if len(symbols) > args.limit:
                print(f"   Limiting from {len(symbols)} to {args.limit} symbols")
                symbols = symbols[:args.limit]
            
            print(f"   Fetching {len(symbols)} options...")
            
            # Fetch option board data
            board_data = await fetch_option_board(connector, symbols)
            
            # Sort options for display
            sorted_options = sort_options_for_display(
                board_data["options"],
                sort_by=args.sort_by,
                sort_order=args.sort_order
            )
            
            # Print table
            print_option_board_table(sorted_options, board_data, args.base_coin, selected_expiry)
            
            # Save to file if requested
            if args.save:
                save_to_markdown(sorted_options, board_data, args.save, args.base_coin, selected_expiry)
            
            # Print summary
            print(f"\n[SUCCESS] Analysis complete!")
            print(f"   Underlying {args.base_coin}: ${board_data['underlying_price']:,.2f}")
            print(f"   Successful options: {board_data['successful_count']}")
            
            if board_data['failed_count'] > 0:
                print(f"   Failed options: {board_data['failed_count']}")
                for failed in board_data['failed_symbols'][:5]:  # Show first 5 failures
                    print(f"     - {failed['symbol']}: {failed['error']}")
                if board_data['failed_count'] > 5:
                    print(f"     ... and {board_data['failed_count'] - 5} more")
    
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
"""
Option Board Fetcher - JSON Format
Get complete option board for BTC-2JAN26 with strikes 75000-110000 in JSON format

Usage:
    python get_option_board_json.py
    python get_option_board_json.py --type call
    python get_option_board_json.py --min-strike 80000 --max-strike 90000
    python get_option_board_json.py > option_board.json
"""

import asyncio
import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bybit_options.services.bybit_connector import BybitConnector
from option_board_utils import (
    generate_option_symbols,
    parse_option_symbol,
    format_option_display,
    calculate_board_statistics,
    sort_options_for_display
)


async def fetch_option_board_json(
    connector: BybitConnector,
    symbols: List[str],
    batch_size: int = 20
) -> Dict[str, Any]:
    """
    Fetch option data for a list of symbols and return as JSON structure
    
    Args:
        connector: BybitConnector instance
        symbols: List of option symbols
        batch_size: Number of symbols to fetch in parallel
    
    Returns:
        Complete JSON structure with option board data
    """
    all_options = []
    successful_symbols = []
    failed_symbols = []
    
    # Get underlying BTC price
    btc_tickers = await connector.get_tickers(category="spot", symbol="BTCUSDT")
    underlying_price = 0
    if btc_tickers and len(btc_tickers) > 0:
        underlying_price = float(btc_tickers[0].get("lastPrice", 0))
    
    # Process symbols in batches
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        
        # Fetch all tickers in parallel
        tasks = [
            connector.get_tickers(category="option", symbol=symbol)
            for symbol in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for symbol, result in zip(batch, results):
            if isinstance(result, Exception):
                failed_symbols.append({
                    "symbol": symbol,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            if not result:
                failed_symbols.append({
                    "symbol": symbol,
                    "error": "No data returned",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            ticker = result[0]
            
            try:
                symbol_data = parse_option_symbol(symbol)
                option_data = format_option_display(symbol_data, ticker, underlying_price)
                all_options.append(option_data)
                successful_symbols.append(symbol)
            except Exception as e:
                failed_symbols.append({
                    "symbol": symbol,
                    "error": f"Processing error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Calculate statistics
    statistics = calculate_board_statistics(all_options)
    
    # Build complete response
    response = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "generator": "bybit-options-risk-engine",
            "version": "1.0.0"
        },
        "request": {
            "base_coin": "BTC",
            "expiry": "2JAN26",
            "strike_range": {
                "min": min(symbols, key=lambda x: parse_option_symbol(x)["strike"]) if symbols else 0,
                "max": max(symbols, key=lambda x: parse_option_symbol(x)["strike"]) if symbols else 0,
                "step": 1000  # Default, could be calculated
            },
            "symbols_requested": len(symbols),
            "option_types": list(set(parse_option_symbol(s)["option_type_name"] for s in symbols))
        },
        "market_data": {
            "underlying_price": underlying_price,
            "underlying_symbol": "BTCUSDT",
            "price_timestamp": datetime.now().isoformat()
        },
        "results": {
            "successful_count": len(successful_symbols),
            "failed_count": len(failed_symbols),
            "success_rate": len(successful_symbols) / len(symbols) if symbols else 0
        },
        "statistics": statistics,
        "options": all_options,
        "failed_symbols": failed_symbols
    }
    
    # Add strike distribution
    if all_options:
        strikes = sorted(set(option["strike"] for option in all_options))
        response["statistics"]["strike_distribution"] = {
            "count": len(strikes),
            "min": min(strikes),
            "max": max(strikes),
            "strikes": strikes
        }
    
    return response


async def main():
    """Main execution function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Fetch BTC-2JAN26 option board in JSON format")
    parser.add_argument("--type", choices=["all", "call", "put"], default="all",
                       help="Option type to fetch (default: all)")
    parser.add_argument("--min-strike", type=int, default=75000,
                       help="Minimum strike price (default: 75000)")
    parser.add_argument("--max-strike", type=int, default=110000,
                       help="Maximum strike price (default: 110000)")
    parser.add_argument("--step", type=int, default=1000,
                       help="Strike price step (default: 1000)")
    parser.add_argument("--output", type=str,
                       help="Output file (default: stdout)")
    parser.add_argument("--indent", type=int, default=2,
                       help="JSON indentation (default: 2)")
    parser.add_argument("--sort-by", choices=["strike", "mark_price", "delta", "iv", "spread"],
                       default="strike", help="Sort options by field")
    parser.add_argument("--sort-order", choices=["asc", "desc"], default="asc",
                       help="Sort order")
    
    args = parser.parse_args()
    
    # Determine option types
    if args.type == "call":
        option_types = ["C"]
    elif args.type == "put":
        option_types = ["P"]
    else:
        option_types = ["C", "P"]
    
    # Generate symbols
    symbols = generate_option_symbols(
        base_coin="BTC",
        expiry="2JAN26",
        min_strike=args.min_strike,
        max_strike=args.max_strike,
        step=args.step,
        option_types=option_types
    )
    
    print(f"[INFO] Fetching {len(symbols)} options for JSON output...", file=sys.stderr)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        error_response = {
            "error": "BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env",
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        print(json.dumps(error_response, indent=args.indent))
        sys.exit(1)
    
    # Fetch data
    try:
        async with BybitConnector(api_key, api_secret, testnet=False) as connector:
            board_data = await fetch_option_board_json(connector, symbols)
            
            # Sort options if requested
            if args.sort_by != "strike" or args.sort_order != "asc":
                board_data["options"] = sort_options_for_display(
                    board_data["options"],
                    sort_by=args.sort_by,
                    sort_order=args.sort_order
                )
            
            # Add sorting info to metadata
            board_data["metadata"]["sorting"] = {
                "by": args.sort_by,
                "order": args.sort_order
            }
            
            # Output JSON
            json_output = json.dumps(board_data, indent=args.indent)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"[SAVED] JSON saved to: {args.output}", file=sys.stderr)
            else:
                print(json_output)
            
            # Print summary to stderr
            print(f"\n[SUCCESS] JSON generation complete!", file=sys.stderr)
            print(f"   Options fetched: {board_data['results']['successful_count']}", file=sys.stderr)
            print(f"   Underlying BTC: ${board_data['market_data']['underlying_price']:,.2f}", file=sys.stderr)
            
            if board_data['results']['failed_count'] > 0:
                print(f"   Failed: {board_data['results']['failed_count']}", file=sys.stderr)
    
    except KeyboardInterrupt:
        error_response = {
            "error": "Analysis interrupted by user",
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        print(json.dumps(error_response, indent=args.indent))
        sys.exit(0)
    
    except Exception as e:
        error_response = {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        print(json.dumps(error_response, indent=args.indent))
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
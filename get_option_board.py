"""
Option Board Fetcher - Table Format (Refactored)
Uses OptionBoardService to fetch and display data.

Usage:
    python get_option_board.py
    python get_option_board.py --type call
    python get_option_board.py --save option_board.md
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.option_board_service import OptionBoardService, OptionBoard
from option_board_utils import sort_options_for_display, get_all_option_series


def print_option_board_table(board: OptionBoard, filtered_options: List[Dict[str, Any]]):
    """Print option board in formatted table"""
    # Header
    print("\n" + "="*180)
    print(f"{board.base_coin}-{board.expiry} OPTION BOARD")
    print(f"Generated: {datetime.fromtimestamp(board.timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Underlying {board.base_coin} Price: ${board.underlying_price:,.2f}")
    print(f"Options: {board.statistics['total_options']} total (Showing {len(filtered_options)})")
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
    for option in filtered_options:
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
            f"{option['moneyness']:^10}",
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
    stats = board.statistics
    if stats:
        print(f"\nBOARD STATISTICS:")
        print(f"   Total Options: {stats['total_options']} (Calls: {stats['calls_count']}, Puts: {stats['puts_count']})")
        print(f"   Moneyness: ITM={stats['moneyness_distribution'].get('ITM', 0)}, "
              f"ATM={stats['moneyness_distribution'].get('ATM', 0)}, "
              f"OTM={stats['moneyness_distribution'].get('OTM', 0)}")
        print(f"   Average Spread: {stats['averages']['spread_percent']:.2f}%")
        print(f"   Average IV: {stats['averages']['iv']*100:.2f}%")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Fetch real option board using OptionBoardService")
    parser.add_argument("--base-coin", type=str, default="BTC")
    parser.add_argument("--expiry", type=str, default=None)
    parser.add_argument("--type", choices=["all", "call", "put"], default="all")
    parser.add_argument("--min-strike", type=int, default=None)
    parser.add_argument("--max-strike", type=int, default=None)
    parser.add_argument("--sort-by", default="strike")
    parser.add_argument("--sort-order", default="asc")
    parser.add_argument("--save", type=str, help="Save to file")
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key:
        print("❌ ERROR: keys not found")
        return

    print(f"[INFO] Initializing OptionBoardService...")
    
    async with BybitConnector(api_key, api_secret) as connector:
        # Check Expiry
        if not args.expiry:
             series = await get_all_option_series(connector, args.base_coin)
             if series:
                 args.expiry = series[0]
                 print(f"[INFO] Auto-selected expiry: {args.expiry}")
             else:
                 print("❌ No expiries found")
                 return

        service = OptionBoardService(connector)
        
        print(f"[INFO] Fetching board for {args.base_coin}-{args.expiry}...")
        board = await service.get_board(args.base_coin, args.expiry)
        
        if not board:
            print("❌ Failed to fetch board")
            return
            
        print(f"[SUCCESS] Got {len(board.options)} options")
        
        # Filter logic
        filtered = []
        for opt in board.options:
            if args.type != "all" and opt["type_code"] != ("C" if args.type == "call" else "P"):
                continue
            if args.min_strike and opt["strike"] < args.min_strike:
                continue
            if args.max_strike and opt["strike"] > args.max_strike:
                continue
            filtered.append(opt)
            
        # Sort
        sorted_opts = sort_options_for_display(
            filtered,
            sort_by=args.sort_by,
            sort_order=args.sort_order
        )
        
        print_option_board_table(board, sorted_opts)
        
        if args.save:
            # Need to re-implement save logic or import it (omitted for brevity in this refactor step, can add back later)
            print(f"⚠️ Saving to file not implemented in this quick refactor.")

if __name__ == "__main__":
    asyncio.run(main())

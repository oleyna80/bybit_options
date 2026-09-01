"""
Option Board Utilities
Common functions for working with option symbols and data
"""

import asyncio
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


def generate_option_symbols(
    base_coin: str = "BTC",
    expiry: str = "2JAN26",
    min_strike: int = 75000,
    max_strike: int = 110000,
    step: int = 1000,
    option_types: List[str] = ["C", "P"]
) -> List[str]:
    """
    Generate option symbols for a given range of strikes
    
    Args:
        base_coin: Base currency (e.g., "BTC")
        expiry: Expiry date in format "DDMMMYY" (e.g., "2JAN26")
        min_strike: Minimum strike price
        max_strike: Maximum strike price
        step: Strike price step
        option_types: List of option types ("C" for call, "P" for put)
    
    Returns:
        List of option symbols in format "BTC-2JAN26-75000-C"
    
    Example:
        >>> generate_option_symbols(min_strike=75000, max_strike=76000, step=1000)
        ['BTC-2JAN26-75000-C', 'BTC-2JAN26-75000-P',
         'BTC-2JAN26-76000-C', 'BTC-2JAN26-76000-P']
    """
    symbols = []
    
    for strike in range(min_strike, max_strike + 1, step):
        for option_type in option_types:
            symbol = f"{base_coin}-{expiry}-{strike}-{option_type}"
            symbols.append(symbol)
    
    return symbols


def parse_option_symbol(symbol: str) -> Dict[str, Any]:
    """
    Parse an option symbol into its components
    
    Args:
        symbol: Option symbol (e.g., "BTC-2JAN26-75000-C" or "BTC-2JAN26-75000-C-USDT")
    
    Returns:
        Dictionary with parsed components:
        {
            "base_coin": "BTC",
            "expiry": "2JAN26",
            "strike": 75000,
            "option_type": "C",
            "full_symbol": "BTC-2JAN26-75000-C-USDT"
        }
    
    Raises:
        ValueError: If symbol format is invalid
    """
    # Remove -USDT suffix if present
    clean_symbol = symbol.replace("-USDT", "")
    
    # Parse using regex
    pattern = r"^([A-Z]+)-(\d+[A-Z]+\d+)-(\d+)-([CP])$"
    match = re.match(pattern, clean_symbol)
    
    if not match:
        raise ValueError(f"Invalid option symbol format: {symbol}")
    
    base_coin, expiry, strike_str, option_type = match.groups()
    
    return {
        "base_coin": base_coin,
        "expiry": expiry,
        "strike": int(strike_str),
        "option_type": option_type,
        "option_type_name": "call" if option_type == "C" else "put",
        "full_symbol": f"{clean_symbol}-USDT",
        "clean_symbol": clean_symbol
    }


def calculate_moneyness(
    strike: float,
    underlying_price: float,
    option_type: str
) -> str:
    """
    Calculate moneyness of an option (ITM, ATM, OTM)
    
    Args:
        strike: Option strike price
        underlying_price: Current underlying price
        option_type: "C" for call, "P" for put
    
    Returns:
        Moneyness string: "ITM" (in-the-money), "ATM" (at-the-money), or "OTM" (out-of-the-money)
    """
    if option_type == "C":
        # For calls: ITM if strike < underlying, OTM if strike > underlying
        if strike < underlying_price * 0.995:  # 0.5% tolerance for ATM
            return "ITM"
        elif strike > underlying_price * 1.005:
            return "OTM"
        else:
            return "ATM"
    else:  # option_type == "P"
        # For puts: ITM if strike > underlying, OTM if strike < underlying
        if strike > underlying_price * 1.005:
            return "ITM"
        elif strike < underlying_price * 0.995:
            return "OTM"
        else:
            return "ATM"


def format_option_display(
    symbol_data: Dict[str, Any],
    ticker_data: Dict[str, Any],
    underlying_price: float
) -> Dict[str, Any]:
    """
    Format option data for display
    
    Args:
        symbol_data: Parsed symbol data from parse_option_symbol
        ticker_data: Raw ticker data from Bybit API
        underlying_price: Current underlying price
    
    Returns:
        Formatted option data dictionary
    """
    # Extract data from ticker
    bid_price = float(ticker_data.get("bid1Price", 0))
    ask_price = float(ticker_data.get("ask1Price", 0))
    mark_price = float(ticker_data.get("markPrice", 0))
    last_price = float(ticker_data.get("lastPrice", 0))
    
    bid_iv = float(ticker_data.get("bid1Iv", 0))
    ask_iv = float(ticker_data.get("ask1Iv", 0))
    mark_iv = float(ticker_data.get("markIv", 0))
    
    delta = float(ticker_data.get("delta", 0))
    gamma = float(ticker_data.get("gamma", 0))
    vega = float(ticker_data.get("vega", 0))
    theta = float(ticker_data.get("theta", 0))
    
    open_interest = float(ticker_data.get("openInterest", 0))
    bid_size = float(ticker_data.get("bid1Size", 0))
    ask_size = float(ticker_data.get("ask1Size", 0))
    volume_24h = float(ticker_data.get("volume24h", 0))
    turnover_24h = float(ticker_data.get("turnover24h", 0))
    
    # Calculate spread
    spread_abs = ask_price - bid_price if ask_price > 0 and bid_price > 0 else 0
    spread_pct = (spread_abs / mark_price * 100) if mark_price > 0 else 0
    
    # Calculate moneyness
    moneyness = calculate_moneyness(
        symbol_data["strike"],
        underlying_price,
        symbol_data["option_type"]
    )
    
    # Calculate intrinsic and extrinsic value
    if symbol_data["option_type"] == "C":
        intrinsic = max(0, underlying_price - symbol_data["strike"])
    else:  # Put
        intrinsic = max(0, symbol_data["strike"] - underlying_price)
    
    extrinsic = mark_price - intrinsic if mark_price > intrinsic else 0
    
    return {
        "symbol": symbol_data["full_symbol"],
        "clean_symbol": symbol_data["clean_symbol"],
        "base_coin": symbol_data["base_coin"],
        "expiry": symbol_data["expiry"],
        "strike": symbol_data["strike"],
        "type": symbol_data["option_type_name"],
        "type_code": symbol_data["option_type"],
        "moneyness": moneyness,
        "prices": {
            "mark": round(mark_price, 2),
            "bid": round(bid_price, 2),
            "ask": round(ask_price, 2),
            "last": round(last_price, 2),
            "underlying": round(underlying_price, 2)
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
        },
        "value_analysis": {
            "intrinsic": round(intrinsic, 2),
            "extrinsic": round(extrinsic, 2),
            "extrinsic_percent": round((extrinsic / mark_price * 100) if mark_price > 0 else 0, 2)
        }
    }


def calculate_board_statistics(options_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for the option board
    
    Args:
        options_data: List of formatted option data
        
    Returns:
        Statistics dictionary
    """
    if not options_data:
        return {}
    
    calls = [o for o in options_data if o["type"] == "call"]
    puts = [o for o in options_data if o["type"] == "put"]
    
    # Calculate averages
    avg_spread = sum(o["spread"]["percent"] for o in options_data) / len(options_data)
    avg_iv = sum(o["iv"]["mark"] for o in options_data) / len(options_data)
    
    # Count by moneyness
    moneyness_counts = {}
    for moneyness in ["ITM", "ATM", "OTM"]:
        moneyness_counts[moneyness] = len([o for o in options_data if o["moneyness"] == moneyness])
    
    # Find most liquid options
    sorted_by_oi = sorted(options_data, key=lambda x: x["liquidity"]["open_interest"], reverse=True)
    sorted_by_volume = sorted(options_data, key=lambda x: x["liquidity"]["volume_24h"], reverse=True)
    
    return {
        "total_options": len(options_data),
        "calls_count": len(calls),
        "puts_count": len(puts),
        "moneyness_distribution": moneyness_counts,
        "averages": {
            "spread_percent": round(avg_spread, 4),
            "iv": round(avg_iv, 6)
        },
        "most_liquid": {
            "by_open_interest": sorted_by_oi[0]["clean_symbol"] if sorted_by_oi else None,
            "by_volume": sorted_by_volume[0]["clean_symbol"] if sorted_by_volume else None
        }
    }


def sort_options_for_display(
    options_data: List[Dict[str, Any]],
    sort_by: str = "strike",
    sort_order: str = "asc"
) -> List[Dict[str, Any]]:
    """
    Sort options data for display
    
    Args:
        options_data: List of formatted option data
        sort_by: Field to sort by ("strike", "mark_price", "delta", "iv", "spread")
        sort_order: "asc" for ascending, "desc" for descending
    
    Returns:
        Sorted list of options data
    """
    if not options_data:
        return []
    
    # Define sort keys
    sort_keys = {
        "strike": lambda x: x["strike"],
        "mark_price": lambda x: x["prices"]["mark"],
        "delta": lambda x: abs(x["greeks"]["delta"]),
        "iv": lambda x: x["iv"]["mark"],
        "spread": lambda x: x["spread"]["percent"]
    }
    
    if sort_by not in sort_keys:
        sort_by = "strike"
    
    sorted_data = sorted(options_data, key=sort_keys[sort_by], reverse=(sort_order == "desc"))
    
    # For strike sorting, also sort by type (calls then puts)
    if sort_by == "strike":
        sorted_data = sorted(sorted_data, key=lambda x: (x["strike"], 0 if x["type"] == "call" else 1))
    
    return sorted_data


async def get_all_option_series(connector, base_coin: str = "BTC") -> list:
     """
     Получить список всех доступных серий опционов
     
     Args:
         connector: BybitConnector instance
         base_coin: Base coin (BTC, ETH, etc)
     
     Returns:
         List of expiry dates (series) in format "DDMMMYY"
     """
     try:
         instruments = await connector.get_instruments_info(
             category="option",
             base_coin=base_coin
         )
         
         logger.info(f"[GET_ALL_OPTION_SERIES] get_instruments_info returned {len(instruments)} instruments for {base_coin}")
         
         # Extract unique expiry dates
         expiries = set()
         for instrument in instruments:
             symbol = instrument.get("symbol", "")
             # Parse symbol to extract expiry (e.g., BTC-2JAN26-75000-C-USDT)
             if "-" in symbol:
                 parts = symbol.split("-")
                 if len(parts) >= 3:
                     expiry = parts[1]  # Second part is expiry like "2JAN26"
                     expiries.add(expiry)
         
         # Convert to sorted list (Chronological sort)
         def parse_expiry_date(expiry_str: str) -> datetime:
             try:
                 # Parse DDMMMYY (e.g., 2JAN26)
                 return datetime.strptime(expiry_str, "%d%b%y")
             except ValueError:
                 return datetime.max
        
         sorted_expiries = sorted(list(expiries), key=parse_expiry_date)
         logger.info(f"[GET_ALL_OPTION_SERIES] Found {len(sorted_expiries)} unique option series for {base_coin}: {sorted_expiries}")
         return sorted_expiries
     
     except Exception as e:
         logger.error(f"[GET_ALL_OPTION_SERIES] Failed to get option series for {base_coin}: {e}", exc_info=True)
         return []


def _normalize_option_symbol(symbol: str) -> str:
    """Ensure option symbol has a single settlement suffix for API calls."""
    for suffix in ("-USDT", "-USDC", "-USD"):
        if symbol.endswith(suffix):
            return symbol
    return f"{symbol}-USDT"


async def fetch_option_tickers(connector, symbols: List[str], batch_size: int = 20) -> Dict[str, Dict[str, Any]]:
    """
    Fetch ticker data for multiple option symbols in batches

    Args:
        connector: BybitConnector instance
        symbols: List of option symbols
        batch_size: Number of symbols to fetch in parallel

    Returns:
        Dictionary mapping symbol to ticker data
    """
    logger.info(f"[FETCH_OPTION_TICKERS] Starting to fetch {len(symbols)} symbols in batches of {batch_size}")
    results = {}

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logger.info(f"[FETCH_OPTION_TICKERS] Processing batch {i//batch_size + 1}: {len(batch)} symbols")

        # Fetch all tickers in parallel - ensure single settlement suffix.
        tasks = [
            connector.get_tickers(category="option", symbol=_normalize_option_symbol(symbol))
            for symbol in batch
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful = 0
        failed = 0
        for symbol, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                logger.warning(f"[FETCH_OPTION_TICKERS] Failed to fetch ticker for {symbol}: {result}")
                failed += 1
                continue

            if not result:
                logger.warning(f"[FETCH_OPTION_TICKERS] No data returned for {symbol}")
                failed += 1
                continue

            ticker = result[0] if result else {}
            results[symbol] = ticker
            successful += 1

        logger.info(
            f"[FETCH_OPTION_TICKERS] Batch {i//batch_size + 1}: "
            f"{successful} successful, {failed} failed. Total results: {len(results)}"
        )

    logger.info(f"[FETCH_OPTION_TICKERS] Finished fetching tickers. Total results: {len(results)}")
    return results


if __name__ == "__main__":
    # Test the functions
    symbols = generate_option_symbols(min_strike=75000, max_strike=76000, step=1000)
    print("Generated symbols:", symbols)
    
    for symbol in symbols[:2]:
        parsed = parse_option_symbol(symbol)
        print(f"Parsed {symbol}:", parsed)
        
        # Test moneyness calculation
        moneyness = calculate_moneyness(parsed["strike"], 86000, parsed["option_type"])
        print(f"Moneyness for strike {parsed['strike']} at 86000: {moneyness}")

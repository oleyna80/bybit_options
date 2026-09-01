
import asyncio
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Portfolio Data from latest_analysis.md (Stale)
# Format: Symbol, Entry Price, Size, Side
POSITIONS = [
    {"symbol": "BTC-27FEB26-93000-C-USDT", "entry": 2735.00, "size": 0.1, "side": "Buy"},
    {"symbol": "BTC-27FEB26-101000-C-USDT", "entry": 920.70, "size": 0.24, "side": "Sell"},
    {"symbol": "BTC-26JUN26-100000-C-USDT", "entry": 6300.00, "size": 0.03, "side": "Buy"},
    {"symbol": "BTC-27FEB26-107000-C-USDT", "entry": 415.62, "size": 0.24, "side": "Buy"},
    {"symbol": "BTC-27FEB26-76000-P-USDT", "entry": 679.38, "size": 0.24, "side": "Buy"},
    {"symbol": "BTC-27FEB26-82000-P-USDT", "entry": 1501.04, "size": 0.24, "side": "Sell"}, # The problematic one
    {"symbol": "BTC-26JUN26-80000-P-USDT", "entry": 5253.33, "size": 0.03, "side": "Buy"}
]

async def fetch_ticker(session, symbol):
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "option", "symbol": symbol}
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        if data['retCode'] == 0 and data['result']['list']:
            return data['result']['list'][0]
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Fetch Spot Price
        async with session.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT") as resp:
            data = await resp.json()
            spot_price = float(data['result']['list'][0]['lastPrice'])
            
        print(f"\nREAL-TIME PORTFOLIO UPDATE")
        print(f"Current BTC Spot: ${spot_price:,.2f}")
        print("-" * 100)
        print(f"{'Symbol':<30} | {'Side':<4} | {'Entry':<8} | {'Mark':<8} | {'PnL ($)':<10} | {'PnL (%)':<8} | {'Status'}")
        print("-" * 100)
        
        total_pnl = 0
        
        for pos in POSITIONS:
            ticker = await fetch_ticker(session, pos['symbol'])
            if not ticker:
                print(f"{pos['symbol']:<30} | N/A (Failed to fetch)")
                continue
                
            mark_price = float(ticker.get('markPrice', 0))
            
            # PnL Calc
            if pos['side'] == 'Buy':
                # Long: (Mark - Entry) * Size
                pnl = (mark_price - pos['entry']) * pos['size']
                roi = ((mark_price - pos['entry']) / pos['entry']) * 100
            else:
                # Short: (Entry - Mark) * Size
                pnl = (pos['entry'] - mark_price) * pos['size']
                roi = ((pos['entry'] - mark_price) / pos['entry']) * 100 # ROI on collateral? Or on Premium? Typically % of Premium captured.
                # If Price doubles, Short PnL is -100% of Premium? No, we assume ROI relative to Premium captured.
                # PnL % = (Profit / Initial Credit) 
                
            total_pnl += pnl
            
            status = "🟢" if pnl >= 0 else "🔴"
            
            print(f"{pos['symbol']:<30} | {pos['side']:<4} | ${pos['entry']:<7.2f} | ${mark_price:<7.2f} | ${pnl:<9.2f} | {roi:<7.1f}% | {status}")
            
        print("-" * 100)
        print(f"TOTAL ESTIMATED PnL: ${total_pnl:.2f}")

if __name__ == "__main__":
    asyncio.run(main())

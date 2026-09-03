
import asyncio
import aiohttp
from datetime import datetime

# Portfolio tracked positions
POSITIONS = [
    {'symbol': 'BTC-27FEB26-93000-C-USDT', 'entry': 2735.00, 'size': 0.1, 'side': 'Buy'},
    {'symbol': 'BTC-27FEB26-101000-C-USDT', 'entry': 920.70, 'size': 0.24, 'side': 'Sell'},
    {'symbol': 'BTC-26JUN26-100000-C-USDT', 'entry': 6300.00, 'size': 0.03, 'side': 'Buy'},
    {'symbol': 'BTC-27FEB26-107000-C-USDT', 'entry': 415.62, 'size': 0.24, 'side': 'Buy'},
    {'symbol': 'BTC-27FEB26-76000-P-USDT', 'entry': 679.38, 'size': 0.24, 'side': 'Buy'},
    {'symbol': 'BTC-27FEB26-82000-P-USDT', 'entry': 1501.04, 'size': 0.24, 'side': 'Sell'},
    {'symbol': 'BTC-26JUN26-80000-P-USDT', 'entry': 5253.33, 'size': 0.03, 'side': 'Buy'}
]

async def main():
    async with aiohttp.ClientSession() as s:
        # 1. Get BTC Spot Price
        async with s.get('https://api.bybit.com/v5/market/tickers', params={'category':'linear','symbol':'BTCUSDT'}) as r:
            d = await r.json()
            spot = float(d['result']['list'][0]['lastPrice'])
        
        # 2. Get All Options Tickers (Batch fetch is efficient)
        async with s.get('https://api.bybit.com/v5/market/tickers', params={'category':'option','baseCoin':'BTC'}) as r:
            d = await r.json()
            tickers = {t['symbol']: t for t in d['result']['list']}
        
        # 3. Build Report
        report_lines = []
        report_lines.append(f"# 🛡️ Options Portfolio Report")
        report_lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC  ")
        report_lines.append(f"**BTC Spot:** ${spot:,.2f}  ")
        report_lines.append("")
        
        # Accumulators
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        total_pnl = 0.0
        
        # Table Header
        table_rows = []
        table_rows.append("| Symbol | Side | Size | Mark | PnL ($) | Delta | Gamma | Theta | Vega |")
        table_rows.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for pos in POSITIONS:
            t = tickers.get(pos['symbol'])
            if not t:
                table_rows.append(f"| `{pos['symbol']}` | {pos['side']} | {pos['size']} | N/A | N/A | N/A | N/A | N/A | N/A |")
                continue
            
            # Market Data
            mark = float(t.get('markPrice', 0))
            delta = float(t.get('delta', 0))
            gamma = float(t.get('gamma', 0))
            theta = float(t.get('theta', 0))
            vega = float(t.get('vega', 0))
            
            # PnL Calculation
            if pos['side'] == 'Buy':
                pnl = (mark - pos['entry']) * pos['size']
                sign = 1
            else:
                pnl = (pos['entry'] - mark) * pos['size']
                sign = -1
            
            # Weighted Greeks (Per Position)
            w_delta = delta * pos['size'] * sign
            w_gamma = gamma * pos['size'] * sign
            w_theta = theta * pos['size'] * sign
            w_vega = vega * pos['size'] * sign
            
            # Accumulate
            total_delta += w_delta
            total_gamma += w_gamma
            total_theta += w_theta
            total_vega += w_vega
            total_pnl += pnl
            
            status = "🟢" if pnl >= 0 else "🔴"
            
            # Add Row
            table_rows.append(f"| `{pos['symbol']}` | {pos['side']} | {pos['size']} | ${mark:.2f} | **${pnl:+.2f}** {status} | {w_delta:+.3f} | {w_gamma:+.6f} | {w_theta:+.2f} | {w_vega:+.2f} |")
            
        # 4. Summary Section
        report_lines.append("## 1. Portfolio Greeks & PnL")
        report_lines.append("| Metric | Net Value | Status |")
        report_lines.append("| :--- | :--- | :--- |")
        report_lines.append(f"| **Total PnL** | **${total_pnl:+.2f}** | {'🟢 Profit' if total_pnl >= 0 else '🔴 Loss'} |")
        report_lines.append(f"| **Net Delta** | **{total_delta:+.4f} BTC** | {'Long' if total_delta > 0 else 'Short'} |")
        report_lines.append(f"| **Net Gamma** | **{total_gamma:+.6f}** | {'Long Vol' if total_gamma > 0 else 'Short Vol'} |")
        report_lines.append(f"| **Net Theta** | **${total_theta:+.2f}/day** | {'paying' if total_theta < 0 else 'collecting'} time |")
        report_lines.append(f"| **Net Vega** | **${total_vega:+.2f}/1%** | {'Long Vol' if total_vega > 0 else 'Short Vol'} |")
        report_lines.append("")
        
        report_lines.append("## 2. Position Details")
        report_lines.extend(table_rows)
        report_lines.append("")
        
        # 5. Risk Commentary
        report_lines.append("## 3. Automated Risk Diagnostics")
        
        # Delta Check
        if abs(total_delta) > 0.1:
            report_lines.append(f"> [!WARNING]")
            report_lines.append(f"> **High Delta Exposure:** {total_delta:+.4f} BTC. You are effectively leveraged long/short spot. Consider hedging.")
        elif abs(total_delta) < 0.05:
             report_lines.append(f"> [!TIP]")
             report_lines.append(f"> **Delta Neutral:** Good job. The portfolio is delta balanced.")
        
        # Theta Check
        if total_theta < 0:
            report_lines.append(f"> [!CAUTION]")
            report_lines.append(f"> **Negative Theta:** You are PAYING ${abs(total_theta):.2f} per day. An Options Portfolio should usually be Theta Positive (Selling Time).")
        
        # Gamma Check (Short Put 82k specific)
        # We know one position is critical
        short_put_row = next((r for r in table_rows if '82000-P' in r), None)
        if short_put_row and '🔴' in short_put_row:
             report_lines.append(f"> [!IMPORTANT]")
             report_lines.append(f"> **Critical Position:** The Short Put 82k is driving losses. Monitor Gamma.")

        # Print to stdout
        print("\n".join(report_lines))

if __name__ == "__main__":
    asyncio.run(main())

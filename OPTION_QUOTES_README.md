# Option Quotes Fetcher Tools

Quick scripts to get current market data for BTC options from Bybit API for hedge positioning and trading decisions.

## 📊 Available Scripts

### 1. **get_option_quotes.py** - Table Format (Recommended for traders)
Pretty-printed table view optimized for quick visual analysis.

```bash
python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C
```

**Output includes:**
- Mark Price (справедливая цена)
- Bid/Ask Prices & Spread
- Implied Volatility (IV with bid/mark/ask)
- Greeks: Delta, Gamma, Vega, Theta
- Open Interest & Liquidity
- 24h Volume & Turnover

### 2. **get_option_quotes_json.py** - JSON Format (For automation)
Structured JSON output for programmatic processing, logging, and integration.

```bash
python get_option_quotes_json.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C
python get_option_quotes_json.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C > quotes.json
```

**Output structure:**
```json
{
  "timestamp": "2025-12-15T23:50:58.915224",
  "success": true,
  "quotes": [
    {
      "symbol": "BTC-19DEC25-82000-P-USDT",
      "prices": { "mark": 451.39, "bid": 450.0, "ask": 455.0, ... },
      "spread": { "absolute": 5.0, "percent": 1.1077 },
      "iv": { "bid": 0.5521, "mark": 0.5528, "ask": 0.5544 },
      "greeks": { "delta": -0.1779, "gamma": 5.69e-05, "vega": 21.56, "theta": -176.27 },
      "liquidity": { "bid_size": 14.47, "ask_size": 2.68, "open_interest": 77.35, ... }
    }
  ]
}
```

## 🎯 Use Cases

### **Hedge Positioning**
Get exact prices for protective puts:
```bash
python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P
```

### **Call Selling**
Check call premiums and spreads:
```bash
python get_option_quotes.py BTC-19DEC25-89000-C BTC-19DEC25-91000-C
```

### **Volatility Analysis**
Compare IV across strikes:
```bash
python get_option_quotes_json.py BTC-26DEC25-75000-P | grep -i '"iv"'
```

### **Quick Entry Decision**
```bash
python get_option_quotes.py BTC-19DEC25-82000-P  # Single option
```

## 📋 Symbol Format

Option symbols follow this pattern:
```
BTC-DDMMMYY-STRIKE-TYPE-USDT
```

Examples:
- `BTC-19DEC25-82000-P` → Put, Strike 82k, Expiry 19 Dec 2025
- `BTC-19DEC25-89000-C` → Call, Strike 89k, Expiry 19 Dec 2025
- `BTC-26DEC25-75000-P` → Put, Strike 75k, Expiry 26 Dec 2025

**Note:** Scripts automatically add `-USDT` suffix if omitted.

## 🔑 Requirements

1. **Environment Setup** (one-time)
   - `.env` file with `BYBIT_API_KEY` and `BYBIT_API_SECRET`
   - Or set as environment variables

2. **Dependencies** (already in project)
   - `bybit_connector.py` - Bybit API client
   - `python 3.8+` with `asyncio`

## ⚙️ Installation

Already integrated into project. Just run:

```bash
cd /path/to/bybit-options-risk-engine
python get_option_quotes.py [SYMBOLS...]
```

## 📊 Data Breakdown

### Prices
- **Mark**: Fair value (mid-price used internally)
- **Bid**: Best price to sell
- **Ask**: Best price to buy
- **Last**: Last traded price

### Volatility (IV)
- **Bid IV**: IV at bid price
- **Mark IV**: IV at fair value
- **Ask IV**: IV at ask price
- Higher IV = more expensive option

### Greeks
- **Delta** (Δ): Price sensitivity to BTC movement
  - Put: negative (-1 to 0)
  - Call: positive (0 to 1)
  - Interpret as "equivalent BTC contracts"
  
- **Gamma** (Γ): Rate of delta change
  - Higher = faster delta changes with price moves
  
- **Vega** (ν): Price sensitivity to IV changes
  - Higher IV = higher option premium
  
- **Theta** (θ): Time decay per day
  - Negative for longs (cost of carrying)
  - Positive for shorts (profit from decay)

### Liquidity
- **Bid/Ask Size**: Available contracts at bid/ask
- **Spread %**: ((Ask - Bid) / Mark) × 100
  - <1% = Tight (liquid)
  - 1-5% = Normal
  - >5% = Wide (illiquid)
- **Open Interest**: Total open contracts
- **Volume 24h**: Daily trading volume

## 🚀 Examples

### Single option (fast lookup)
```bash
$ python get_option_quotes.py BTC-19DEC25-82000-P
```

### Multiple options for comparison
```bash
$ python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P BTC-19DEC25-86000-P
```

### Export to file for analysis
```bash
$ python get_option_quotes_json.py BTC-19DEC25-82000-P > hedge_prices.json
```

### Programmatic usage (Python)
```python
import asyncio
import json
from get_option_quotes_json import get_option_quotes_json

async def analyze_options():
    result = await get_option_quotes_json(['BTC-19DEC25-82000-P'])
    data = result['quotes'][0]
    print(f"Mark: ${data['prices']['mark']}, Spread: {data['spread']['percent']}%")

asyncio.run(analyze_options())
```

## 💡 Tips for Traders

1. **Compare Spreads**: Wider spreads on less liquid strikes = slippage risk
2. **IV Levels**: High IV = expensive to buy options, good to sell
3. **Greeks**: High gamma near ATM = bigger daily swings in theta
4. **Time Decay**: Theta accelerates as expiry approaches (19 DEC coming soon!)
5. **Recent Data**: Always get fresh quotes before entering positions

## 🐛 Troubleshooting

**"No data" error:**
- Check symbol format is correct
- Verify option expiry hasn't passed
- Check API credentials in .env

**Connection error:**
- Ensure internet connection
- Verify API keys are valid
- Check rate limits (Bybit: 50 requests/second)

**Unexpected prices:**
- Bybit updates mark prices every 100ms
- Quotes refresh on every script run
- For real-time: create a streaming websocket variant

## 📝 License & Attribution

Part of `bybit-options-risk-engine` project.
Uses Bybit V5 Public API for options market data.

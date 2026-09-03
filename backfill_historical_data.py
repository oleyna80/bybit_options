"""
Hybrid Volatility Backfill Script (Fixed Architecture)

STRATEGY:
1. Fetch 2 years of Perpetual Futures OHLCV ✅
2. Calculate Historical Volatility (HV) as proxy for IV (PHASE 1: Bootstrap)
3. Fetch current real ATM IV snapshot (PHASE 2: Real-time data starts today)
4. Calculate IV Rank with outlier-resistant percentile filtering

CRITICAL NOTES:
- Historical data (past 2 years) uses HV as PROXY for IV (not real IV)
- Real IV collection starts from today forward via daily cron
- Percentile filtering prevents flash crash/spike distortion
"""
import asyncio
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bybit_options.services.bybit_connector import BybitConnector
from database import async_engine, AsyncSessionLocal
from config import get_config


class HybridVolatilityBackfiller:
    """
    Backfills historical data with HV proxy + real-time IV collection
    """
    
    def __init__(self):
        self.config = get_config()
        self.connector: Optional[BybitConnector] = None
        
    async def __aenter__(self):
        """Initialize connector on enter"""
        self.connector = BybitConnector(
            api_key=self.config.bybit_api_key,
            api_secret=self.config.bybit_api_secret,
            testnet=self.config.bybit_testnet
        )
        await self.connector._init_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close connector on exit"""
        if self.connector:
            await self.connector.close()
    
    # ========================================================================
    # PHASE 1: Perpetual OHLCV Fetching (UNCHANGED - This part works)
    # ========================================================================
    
    async def fetch_perpetual_klines(
        self,
        symbol: str = "BTCUSDT",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict]:
        """
        Fetch perpetual futures klines (OHLCV) with pagination
        Bybit limit: 200 candles per request
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=730)  # 2 years
        if end_date is None:
            end_date = datetime.now()
            
        all_klines = []
        current_end = end_date
        
        logger.info(f"📊 Fetching perpetual klines from {start_date.date()} to {end_date.date()}")
        
        while current_end > start_date:
            # Calculate start time for this batch (200 days back)
            batch_start = current_end - timedelta(days=200)
            if batch_start < start_date:
                batch_start = start_date
                
            # Convert to milliseconds
            start_ms = int(batch_start.timestamp() * 1000)
            end_ms = int(current_end.timestamp() * 1000)
            
            try:
                # Use the existing connector's method
                await self.connector.rate_limiter.acquire()
                
                endpoint = "/v5/market/kline"
                params = {
                    "category": "linear",
                    "symbol": symbol,
                    "interval": "D",
                    "start": start_ms,
                    "end": end_ms,
                    "limit": 200
                }
                
                response = await self.connector._public_request(endpoint, params=params)
                
                if response.get("retCode") == 0:
                    klines = response["result"]["list"]
                    
                    if not klines:
                        logger.warning(f"No klines returned for period {batch_start.date()} to {current_end.date()}")
                        break
                    
                    all_klines.extend(klines)
                    logger.info(f"   Fetched {len(klines)} candles | Total: {len(all_klines)}")
                    
                    # Move to earlier period
                    current_end = batch_start
                    
                    # Rate limiting delay
                    await asyncio.sleep(0.1)
                else:
                    logger.error(f"API error: {response.get('retMsg')}")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching klines: {e}")
                break
        
        logger.success(f"✅ Total klines fetched: {len(all_klines)}")
        return all_klines
    
    def parse_kline_to_ohlcv(self, kline: List) -> Dict:
        """
        Parse Bybit kline format to OHLCV dict
        Bybit format: [startTime, open, high, low, close, volume, turnover]
        """
        return {
            "timestamp": datetime.fromtimestamp(int(kline[0]) / 1000),
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5])
        }
    
    async def save_perpetual_ohlcv(
        self,
        session: AsyncSession,
        symbol: str,
        klines: List[Dict]
    ):
        """Save perpetual OHLCV to database"""
        logger.info(f"💾 Saving {len(klines)} perpetual candles to database...")
        
        insert_query = text("""
            INSERT INTO perpetual_ohlcv (timestamp, symbol, open, high, low, close, volume, turnover)
            VALUES (:timestamp, :symbol, :open, :high, :low, :close, :volume, :turnover)
            ON CONFLICT (timestamp, symbol) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover
        """)
        
        saved_count = 0
        for kline in klines:
            ohlcv = self.parse_kline_to_ohlcv(kline)
            
            try:
                await session.execute(insert_query, {
                    "timestamp": ohlcv["timestamp"],
                    "symbol": symbol,
                    "open": ohlcv["open"],
                    "high": ohlcv["high"],
                    "low": ohlcv["low"],
                    "close": ohlcv["close"],
                    "volume": ohlcv["volume"],
                    "turnover": float(kline[6]) if len(kline) > 6 else 0.0
                })
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving candle {ohlcv['timestamp']}: {e}")
        
        await session.commit()
        logger.success(f"✅ Saved {saved_count}/{len(klines)} perpetual candles")
    
    # ========================================================================
    # PHASE 2: HISTORICAL VOLATILITY CALCULATION (NEW - HV Proxy)
    # ========================================================================
    
    async def calculate_and_save_historical_volatility(
        self,
        base_coin: str = "BTC",
        window_days: int = 30
    ):
        """
        Calculate Historical Volatility (HV) from OHLCV as proxy for IV
        
        IMPORTANT: This is NOT real Implied Volatility!
        - HV looks backward (realized volatility)
        - IV looks forward (market expectation)
        - Correlation is typically 0.6-0.8
        
        Formula:
        1. Log Returns: ln(Close_t / Close_t-1)
        2. Rolling StdDev: std(log_returns, window=30)
        3. Annualize: std * sqrt(365)
        """
        logger.info(f"📈 Calculating Historical Volatility (HV) as IV proxy...")
        logger.warning(
            "⚠️  PROXY DATA: Historical volatility ≠ Implied Volatility. "
            "This is a bootstrap approximation. Real IV collection starts today."
        )
        
        async with AsyncSessionLocal() as session:
            # Fetch OHLCV data
            query = text("""
                SELECT timestamp, close 
                FROM perpetual_ohlcv 
                WHERE symbol = :symbol 
                ORDER BY timestamp ASC
            """)
            
            result = await session.execute(query, {"symbol": f"{base_coin}USDT"})
            rows = result.fetchall()
            
            if len(rows) < window_days + 1:
                logger.error(
                    f"Not enough OHLCV data. Need {window_days + 1} days, "
                    f"have {len(rows)}. Run perpetual backfill first."
                )
                return
            
            logger.info(f"   Found {len(rows)} days of price data")
            
            # Convert to pandas DataFrame (VECTORIZED - No loops!)
            df = pd.DataFrame(rows, columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Convert Decimal to float (PostgreSQL returns Decimal type)
            df['close'] = df['close'].astype(float)

            # Calculate log returns
            df['log_return'] = np.log(df['close'] / df['close'].shift(1))
            
            # Calculate rolling 30-day HV (annualized)
            df['hv'] = df['log_return'].rolling(window=window_days).std() * np.sqrt(365)
            
            # Drop NaN rows (first 30 days have no HV)
            df_valid = df.dropna(subset=['hv']).copy()
            
            logger.info(f"   Calculated HV for {len(df_valid)} days (dropped first {window_days} NaN)")
            
            # Save to option_iv_daily as PROXY data
            insert_query = text("""
                INSERT INTO option_iv_daily (
                    timestamp, symbol, underlying, strike, expiry_date, 
                    days_to_expiry, option_type, iv, is_atm, mark_price
                )
                VALUES (
                    :timestamp, :symbol, :underlying, :strike, :expiry_date,
                    :days_to_expiry, :option_type, :iv, :is_atm, :mark_price
                )
                ON CONFLICT (timestamp, symbol) DO UPDATE SET
                    iv = EXCLUDED.iv
            """)
            
            saved_count = 0
            for _, row in df_valid.iterrows():
                try:
                    # NOTE: We use synthetic values for strike/expiry since this is HV proxy
                    await session.execute(insert_query, {
                        "timestamp": row['timestamp'].to_pydatetime(),
                        "symbol": f"{base_coin}-HV-PROXY",  # Mark as proxy data
                        "underlying": base_coin,
                        "strike": row['close'],  # Use current price as "ATM"
                        "expiry_date": (row['timestamp'] + pd.Timedelta(days=30)).date(),
                        "days_to_expiry": 30,
                        "option_type": "C",
                        "iv": float(row['hv']),
                        "is_atm": True,
                        "mark_price": 0.0  # Not applicable for HV proxy
                    })
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving HV for {row['timestamp']}: {e}")
            
            await session.commit()
            logger.success(f"✅ Saved {saved_count} HV proxy records to option_iv_daily")
    
    # ========================================================================
    # PHASE 3: REAL-TIME IV SNAPSHOT (NEW - Honest naming)
    # ========================================================================
    
    async def fetch_current_real_iv_snapshot(
        self,
        base_coin: str = "BTC"
    ) -> bool:
        """
        Fetch CURRENT (today's) ATM option IV from live market
        
        IMPORTANT: This is REAL Implied Volatility from the market!
        Unlike HV proxy, this is actual market expectation.
        
        This method should be called:
        1. Once during initial backfill (for today)
        2. Daily via cron job (00:05 UTC)
        """
        logger.info(f"🎯 Fetching REAL ATM IV snapshot for {base_coin}...")
        
        async with AsyncSessionLocal() as session:
            # Get current perpetual price
            price_query = text("""
                SELECT close FROM perpetual_ohlcv 
                WHERE symbol = :symbol 
                ORDER BY timestamp DESC LIMIT 1
            """)
            result = await session.execute(price_query, {"symbol": f"{base_coin}USDT"})
            row = result.fetchone()
            
            if not row:
                logger.error("No perpetual price found. Cannot determine ATM strike.")
                return False
            
            perpetual_price = float(row[0])
            logger.info(f"   Current {base_coin} price: ${perpetual_price:,.2f}")
            
            # Fetch option tickers using built-in method
            try:
                await self.connector.rate_limiter.acquire()
                
                options = await self.connector.get_tickers(
                    category="option",
                    base_coin=base_coin
                )
                
                if not options:
                    logger.error(f"Failed to fetch options for {base_coin}")
                    return False
                
                # Filter ATM options with ~30 days to expiry
                atm_candidates = []
                now = datetime.now()
                
                for opt in options:
                    symbol = opt.get("symbol", "")
                    
                    try:
                        # Parse symbol: BTC-31JAN25-100000-C
                        parts = symbol.split("-")
                        if len(parts) < 4:
                            continue
                        
                        expiry_str = parts[1]
                        expiry_date = datetime.strptime(expiry_str, "%d%b%y")
                        
                        days_to_expiry = (expiry_date - now).days
                        
                        # Filter: 25-35 days (monthly options)
                        if not (25 <= days_to_expiry <= 35):
                            continue
                        
                        strike = float(parts[2])
                        option_type = parts[3]
                        
                        # Only Calls
                        if option_type != "C":
                            continue
                        
                        mark_iv = opt.get("markIv", "0")
                        if mark_iv == "0" or mark_iv == "":
                            continue
                        
                        iv = float(mark_iv)
                        distance = abs(strike - perpetual_price)
                        
                        atm_candidates.append({
                            "symbol": symbol,
                            "strike": strike,
                            "expiry_date": expiry_date,
                            "days_to_expiry": days_to_expiry,
                            "iv": iv,
                            "distance": distance,
                            "mark_price": float(opt.get("markPrice", 0)),
                            "volume": float(opt.get("volume24h", 0))
                        })
                        
                    except Exception as e:
                        logger.debug(f"Skipping option {symbol}: {e}")
                        continue
                
                if not atm_candidates:
                    logger.warning(f"No ATM options found for {base_coin}")
                    return False
                
                # Find closest to ATM
                atm_option = min(atm_candidates, key=lambda x: x["distance"])
                
                # Save to database
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                
                insert_query = text("""
                    INSERT INTO option_iv_daily (
                        timestamp, symbol, underlying, strike, expiry_date, 
                        days_to_expiry, option_type, iv, mark_price, volume,
                        is_atm, distance_to_atm
                    )
                    VALUES (
                        :timestamp, :symbol, :underlying, :strike, :expiry_date,
                        :days_to_expiry, :option_type, :iv, :mark_price, :volume,
                        :is_atm, :distance_to_atm
                    )
                    ON CONFLICT (timestamp, symbol) DO UPDATE SET
                        iv = EXCLUDED.iv,
                        mark_price = EXCLUDED.mark_price,
                        volume = EXCLUDED.volume
                """)
                
                await session.execute(insert_query, {
                    "timestamp": today,
                    "symbol": atm_option["symbol"],
                    "underlying": base_coin,
                    "strike": atm_option["strike"],
                    "expiry_date": atm_option["expiry_date"].date(),
                    "days_to_expiry": atm_option["days_to_expiry"],
                    "option_type": "C",
                    "iv": atm_option["iv"],
                    "mark_price": atm_option["mark_price"],
                    "volume": atm_option["volume"],
                    "is_atm": True,
                    "distance_to_atm": atm_option["distance"]
                })
                
                await session.commit()
                
                logger.success(
                    f"✅ Saved REAL IV: {atm_option['symbol']} "
                    f"IV={atm_option['iv']:.2%} (Strike: ${atm_option['strike']:,.0f})"
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Error fetching real IV snapshot: {e}")
                return False
    
    # ========================================================================
    # PHASE 4: IV RANK CALCULATION (FIXED - Percentile filtering)
    # ========================================================================
    
    async def calculate_and_save_iv_rank(
        self,
        base_coin: str = "BTC",
        period_days: int = 30
    ):
        """
        Calculate IV Rank with ROBUST percentile-based scaling
        
        IMPROVEMENT: Uses 1st/99th percentiles instead of min/max
        This prevents flash crashes and spikes from distorting the entire chart.
        
        Example:
        - Old: One spike to 300% IV makes all other values look tiny
        - New: Cuts off extreme 1% on both ends for stable scaling
        """
        logger.info(f"🎯 Calculating IV Rank with {period_days}-day window...")
        logger.info(f"   Using PERCENTILE filtering (1st/99th) for robustness")
        
        async with AsyncSessionLocal() as session:
            # Get all IV data (both HV proxy and real IV)
            query = text("""
                SELECT timestamp, iv
                FROM option_iv_daily
                WHERE underlying = :base_coin
                    AND is_atm = TRUE
                ORDER BY timestamp ASC
            """)
            
            result = await session.execute(query, {"base_coin": base_coin})
            iv_data = result.fetchall()
            
            if len(iv_data) < period_days:
                logger.warning(
                    f"Not enough data for IV Rank. "
                    f"Need {period_days} days, have {len(iv_data)}"
                )
                return
            
            logger.info(f"   Found {len(iv_data)} days of IV data")
            
            # Convert to numpy for vectorized operations (force float type)
            timestamps = [row[0] for row in iv_data]
            ivs = np.array([float(row[1]) for row in iv_data], dtype=np.float64)
            
            # Calculate IV Rank for each date (vectorized)
            iv_ranks = []
            
            for i in range(period_days - 1, len(ivs)):
                current_date = timestamps[i]
                current_iv = ivs[i]
                
                # Get 30-day window
                window_start = i - period_days + 1
                window_ivs = ivs[window_start:i+1]
                
                # ROBUST SCALING: Use percentiles instead of min/max
                # This cuts off extreme outliers (flash crashes, spikes)
                min_iv = np.percentile(window_ivs, 1)   # 1st percentile
                max_iv = np.percentile(window_ivs, 99)  # 99th percentile
                
                # Calculate IV Rank
                if max_iv == min_iv or max_iv - min_iv < 0.001:  # Handle edge case
                    iv_rank = 50.0
                else:
                    iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
                    iv_rank = max(0.0, min(100.0, iv_rank))  # Clamp to [0, 100]
                
                iv_ranks.append({
                    "timestamp": current_date,
                    "current_iv": float(current_iv),
                    "min_iv_30d": float(min_iv),
                    "max_iv_30d": float(max_iv),
                    "iv_rank": float(iv_rank),
                    "data_points": len(window_ivs)
                })
            
            # Batch insert/update
            insert_query = text("""
                INSERT INTO iv_rank_daily (
                    timestamp, underlying, current_iv, min_iv_30d, max_iv_30d, iv_rank,
                    data_points_count
                )
                VALUES (
                    :timestamp, :underlying, :current_iv, :min_iv_30d, :max_iv_30d, :iv_rank,
                    :data_points_count
                )
                ON CONFLICT (timestamp) DO UPDATE SET
                    current_iv = EXCLUDED.current_iv,
                    min_iv_30d = EXCLUDED.min_iv_30d,
                    max_iv_30d = EXCLUDED.max_iv_30d,
                    iv_rank = EXCLUDED.iv_rank
            """)
            
            saved_count = 0
            for rank_data in iv_ranks:
                try:
                    await session.execute(insert_query, {
                        "timestamp": rank_data["timestamp"],
                        "underlying": base_coin,
                        "current_iv": rank_data["current_iv"],
                        "min_iv_30d": rank_data["min_iv_30d"],
                        "max_iv_30d": rank_data["max_iv_30d"],
                        "iv_rank": rank_data["iv_rank"],
                        "data_points_count": rank_data["data_points"]
                    })
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving IV Rank for {rank_data['timestamp']}: {e}")
            
            await session.commit()
            logger.success(f"✅ Calculated and saved {saved_count} IV Rank values")
            
            # Show sample of recent ranks
            logger.info("\n📊 Sample of recent IV Rank values:")
            for rank_data in iv_ranks[-5:]:
                logger.info(
                    f"   {rank_data['timestamp'].date()} | "
                    f"IV: {rank_data['current_iv']:.2%} | "
                    f"Rank: {rank_data['iv_rank']:.1f} | "
                    f"Range: {rank_data['min_iv_30d']:.2%} - {rank_data['max_iv_30d']:.2%}"
                )
    
    # ========================================================================
    # ORCHESTRATOR: Full Hybrid Backfill
    # ========================================================================
    
    async def run_full_backfill(
        self,
        symbol: str = "BTCUSDT",
        base_coin: str = "BTC",
        days_back: int = 730
    ):
        """
        Execute complete hybrid backfill strategy
        
        WORKFLOW:
        1. Fetch 2 years of perpetual OHLCV
        2. Calculate HV as proxy IV for historical data
        3. Fetch today's REAL IV snapshot
        4. Calculate IV Rank with percentile filtering
        """
        logger.info("=" * 70)
        logger.info(" HYBRID VOLATILITY BACKFILL")
        logger.info("=" * 70)
        logger.info(f"Strategy: HV Proxy (historical) + Real IV (from today)")
        logger.info(f"Target: {symbol} | {days_back} days | {base_coin} options")
        logger.info("=" * 70)
        
        # Step 1: Backfill perpetual OHLCV
        logger.info("\n📊 STEP 1: Fetching Perpetual Futures Data (2 years)...")
        start_date = datetime.now() - timedelta(days=days_back)
        klines = await self.fetch_perpetual_klines(symbol, start_date)
        
        if klines:
            async with AsyncSessionLocal() as session:
                await self.save_perpetual_ohlcv(session, symbol, klines)
        else:
            logger.error("❌ Failed to fetch klines. Aborting.")
            return
        
        # Step 2: Calculate HV as proxy IV
        logger.info("\n📈 STEP 2: Calculating Historical Volatility (HV Proxy)...")
        await self.calculate_and_save_historical_volatility(base_coin)
        
        # Step 3: Fetch today's real IV
        logger.info("\n🎯 STEP 3: Fetching Today's REAL ATM IV Snapshot...")
        real_iv_success = await self.fetch_current_real_iv_snapshot(base_coin)
        
        if real_iv_success:
            logger.success("✅ Real IV saved for today")
        else:
            logger.warning("⚠️  Could not fetch real IV. Using HV only for now.")
        
        # Step 4: Calculate IV Rank
        logger.info("\n🎯 STEP 4: Calculating IV Rank (Percentile-based)...")
        await self.calculate_and_save_iv_rank(base_coin)
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.success("✅ HYBRID BACKFILL COMPLETE!")
        logger.info("=" * 70)
        logger.info("\n📋 SUMMARY:")
        logger.info(f"   • Perpetual OHLCV: {len(klines)} days ✅")
        logger.info(f"   • HV Proxy IV: ~{len(klines) - 30} days ✅")
        logger.info(f"   • Real IV: {'Today ✅' if real_iv_success else 'Pending ⏳'}")
        logger.info(f"   • IV Rank: Calculated with percentile filtering ✅")
        logger.info("\n💡 NEXT STEPS:")
        logger.info("   1. Set up daily cron to run fetch_current_real_iv_snapshot()")
        logger.info("   2. In 30 days, real IV will fully replace HV proxy")
        logger.info("   3. Validate data with: SELECT * FROM iv_rank_daily ORDER BY timestamp DESC LIMIT 10;")
        logger.info("=" * 70)


async def main():
    """Main entry point"""
    try:
        async with HybridVolatilityBackfiller() as backfiller:
            await backfiller.run_full_backfill(
                symbol="BTCUSDT",
                base_coin="BTC",
                days_back=730  # 2 years
            )
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("🚀 Starting Hybrid Volatility Backfill Script...")
    asyncio.run(main())
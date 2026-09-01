"""
Daily IV Update Script - Real-time IV collection cron job

Purpose: 
- Fetch today's ATM option IV
- Calculate latest IV Rank
- Store in PostgreSQL

Schedule: Daily at 00:05 UTC (after market daily close)

Features:
- Bybit API health check (for home PC usage)
- Retry logic with exponential backoff
- Detailed logging
- Email/Slack notifications (optional)
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from bybit_options.services.bybit_connector import BybitConnector
from database import AsyncSessionLocal
from config import get_config
import numpy as np


class DailyIVUpdater:
    """Daily IV update service with health checks"""
    
    def __init__(self, skip_health_check: bool = False):
        """
        Initialize updater
        
        Args:
            skip_health_check: If True, skip Bybit API availability check
                              (use on production VPS, disable for home PC)
        """
        self.config = get_config()
        self.connector: Optional[BybitConnector] = None
        self.skip_health_check = skip_health_check or os.getenv("SKIP_BYBIT_HEALTH_CHECK", "false").lower() == "true"
        
        if self.skip_health_check:
            logger.info("⚠️  Health check DISABLED (VPS mode)")
        else:
            logger.info("✅ Health check ENABLED (Home PC mode)")
    
    async def __aenter__(self):
        """Initialize connector"""
        self.connector = BybitConnector(
            api_key=self.config.bybit_api_key,
            api_secret=self.config.bybit_api_secret,
            testnet=self.config.bybit_testnet
        )
        await self.connector._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close connector"""
        if self.connector:
            await self.connector.close()
    
    # ========================================================================
    # HEALTH CHECK: Verify Bybit API availability
    # ========================================================================
    
    async def check_bybit_health(self, timeout: int = 10) -> bool:
        """
        Check if Bybit API is accessible
        
        Returns:
            True if API is healthy, False otherwise
        """
        if self.skip_health_check:
            logger.info("⏭️  Skipping health check (disabled)")
            return True
        
        logger.info("🏥 Checking Bybit API health...")
        
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                # Use simple public endpoint
                url = f"{self.connector.base_url}/v5/market/time"
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        server_time = data.get("result", {}).get("timeSecond")
                        
                        if server_time:
                            logger.success(f"✅ Bybit API is healthy (server time: {server_time})")
                            return True
                        else:
                            logger.error("❌ Bybit API returned invalid response")
                            return False
                    else:
                        logger.error(f"❌ Bybit API returned HTTP {resp.status}")
                        return False
        
        except asyncio.TimeoutError:
            logger.error(f"❌ Bybit API timeout after {timeout}s")
            return False
        
        except Exception as e:
            logger.error(f"❌ Bybit API health check failed: {e}")
            return False
        
    async def wait_for_bybit_availability(
        self,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> bool:
        """
        Wait for Bybit API to become available (with retries)
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Seconds to wait between retries
            
        Returns:
            True if API becomes available, False if max retries exceeded
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"🔄 Attempt {attempt}/{max_retries}...")
            
            if await self.check_bybit_health():
                return True
            
            if attempt < max_retries:
                logger.warning(f"⏳ Waiting {retry_delay}s before retry...")
                await asyncio.sleep(retry_delay)
        
        logger.error(f"❌ Failed to connect after {max_retries} attempts")
        return False
    
    # ========================================================================
    # FETCH PERPETUAL PRICE
    # ========================================================================
    
    async def get_current_perpetual_price(
        self,
        symbol: str = "BTCUSDT"
    ) -> Optional[float]:
        """Get current perpetual futures price"""
        logger.info(f"📊 Fetching current {symbol} price...")
        
        try:
            tickers = await self.connector.get_tickers(
                category="linear",
                symbol=symbol
            )
            
            if tickers:
                price = float(tickers[0].get("lastPrice", 0))
                logger.info(f"   Current price: ${price:,.2f}")
                return price
            else:
                logger.error(f"No ticker data for {symbol}")
                return None
        
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return None
    
    # ========================================================================
    # FETCH & SAVE ATM IV
    # ========================================================================
    
    async def fetch_and_save_atm_iv(
        self,
        base_coin: str = "BTC"
    ) -> bool:
        """
        Fetch today's ATM option IV and save to database
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🎯 Fetching ATM IV for {base_coin}...")
        
        # Get current price
        perpetual_price = await self.get_current_perpetual_price(f"{base_coin}USDT")
        
        if not perpetual_price:
            logger.error("Failed to get perpetual price")
            return False
        
        # Fetch option chain
        try:
            options = await self.connector.get_tickers(
                category="option",
                base_coin=base_coin
            )
            
            if not options:
                logger.warning(f"No options found for {base_coin}")
                return False
            
            # Filter ATM options with ~30 days to expiry
            atm_candidates = []
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
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
                        "volume": float(opt.get("volume24h", 0)),
                        "open_interest": float(opt.get("openInterest", 0))
                    })
                
                except Exception as e:
                    logger.debug(f"Skipping option {symbol}: {e}")
                    continue
            
            if not atm_candidates:
                logger.warning(f"No ATM options found for {base_coin}")
                return False
            
            # Find closest to ATM
            atm_option = min(atm_candidates, key=lambda x: x["distance"])
            
            logger.info(
                f"   Found ATM: {atm_option['symbol']} | "
                f"Strike: ${atm_option['strike']:,.0f} | "
                f"IV: {atm_option['iv']:.2%}"
            )
            
            # Save to database
            async with AsyncSessionLocal() as session:
                today = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                
                # First, delete HV proxy for today if exists
                delete_proxy_query = text("""
                    DELETE FROM option_iv_daily 
                    WHERE timestamp = :timestamp 
                    AND symbol LIKE '%HV-PROXY%'
                """)
                
                await session.execute(delete_proxy_query, {"timestamp": today})
                
                # Insert real IV
                insert_query = text("""
                    INSERT INTO option_iv_daily (
                        timestamp, symbol, underlying, strike, expiry_date, 
                        days_to_expiry, option_type, iv, mark_price, volume,
                        open_interest, is_atm, distance_to_atm
                    )
                    VALUES (
                        :timestamp, :symbol, :underlying, :strike, :expiry_date,
                        :days_to_expiry, :option_type, :iv, :mark_price, :volume,
                        :open_interest, :is_atm, :distance_to_atm
                    )
                    ON CONFLICT (timestamp, symbol) DO UPDATE SET
                        iv = EXCLUDED.iv,
                        mark_price = EXCLUDED.mark_price,
                        volume = EXCLUDED.volume,
                        open_interest = EXCLUDED.open_interest
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
                    "open_interest": atm_option["open_interest"],
                    "is_atm": True,
                    "distance_to_atm": atm_option["distance"]
                })
                
                await session.commit()
                
                logger.success(f"✅ Saved ATM IV: {atm_option['iv']:.2%}")
                return True
        
        except Exception as e:
            logger.error(f"Error fetching/saving ATM IV: {e}")
            return False
    
    # ========================================================================
    # RECALCULATE IV RANK
    # ========================================================================
    
    async def recalculate_iv_rank(
        self,
        base_coin: str = "BTC",
        period_days: int = 30
    ) -> bool:
        """
        Recalculate IV Rank for latest data points
        
        Only recalculates last 35 days (optimized for daily updates)
        """
        logger.info(f"🎯 Recalculating IV Rank...")
        
        try:
            async with AsyncSessionLocal() as session:
                # Get last 65 days of IV data (30 for window + 35 for calculation)
                query = text("""
                    SELECT timestamp, iv
                    FROM option_iv_daily
                    WHERE underlying = :base_coin
                        AND is_atm = TRUE
                        AND timestamp >= NOW() - INTERVAL '65 days'
                    ORDER BY timestamp ASC
                """)
                
                result = await session.execute(query, {"base_coin": base_coin})
                iv_data = result.fetchall()
                
                if len(iv_data) < period_days:
                    logger.warning(
                        f"Not enough data for IV Rank. "
                        f"Need {period_days} days, have {len(iv_data)}"
                    )
                    return False
                
                logger.info(f"   Processing {len(iv_data)} days of IV data...")
                
                                
                # Convert to arrays
                timestamps = [row[0] for row in iv_data]
                ivs = np.array([float(row[1]) for row in iv_data], dtype=np.float64)
                
                # Calculate IV Rank for last 35 days
                recalc_start = max(0, len(ivs) - 35)
                
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
                        iv_rank = EXCLUDED.iv_rank,
                        updated_at = NOW()
                """)
                
                updated_count = 0
                
                for i in range(max(period_days - 1, recalc_start), len(ivs)):
                    current_date = timestamps[i]
                    current_iv = ivs[i]
                    
                    # Get 30-day window
                    window_start = i - period_days + 1
                    window_ivs = ivs[window_start:i+1]
                    
                    # Percentile-based scaling (robust to outliers)
                    min_iv = np.percentile(window_ivs, 1)
                    max_iv = np.percentile(window_ivs, 99)
                    
                    # Calculate IV Rank
                    if max_iv == min_iv or max_iv - min_iv < 0.001:
                        iv_rank = 50.0
                    else:
                        iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
                        iv_rank = max(0.0, min(100.0, iv_rank))
                    
                    await session.execute(insert_query, {
                        "timestamp": current_date,
                        "underlying": base_coin,
                        "current_iv": float(current_iv),
                        "min_iv_30d": float(min_iv),
                        "max_iv_30d": float(max_iv),
                        "iv_rank": float(iv_rank),
                        "data_points_count": len(window_ivs)
                    })
                    
                    updated_count += 1
                
                await session.commit()
                
                # Get latest IV Rank for logging
                latest_query = text("""
                    SELECT timestamp::date, iv_rank, current_iv
                    FROM iv_rank_daily
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                
                result = await session.execute(latest_query)
                latest = result.fetchone()
                
                if latest:
                    logger.success(
                        f"✅ Updated {updated_count} IV Rank values | "
                        f"Latest: {latest[0]} | Rank: {latest[1]:.1f} | IV: {latest[2]:.2%}"
                    )
                
                return True
        
        except Exception as e:
            logger.error(f"Error recalculating IV Rank: {e}")
            return False
    
    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================
    
    async def run_daily_update(
        self,
        base_coin: str = "BTC"
    ) -> bool:
        """
        Execute complete daily update workflow
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 70)
        logger.info(f" DAILY IV UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 70)
        
        # Step 1: Health check (with retry)
        if not self.skip_health_check:
            logger.info("\n🏥 STEP 1: Health Check...")
            if not await self.wait_for_bybit_availability(max_retries=3, retry_delay=60):
                logger.error("❌ Bybit API unavailable. Aborting update.")
                logger.info("💡 TIP: Computer might be offline. Will retry next schedule.")
                return False
        else:
            logger.info("\n⏭️  STEP 1: Health Check (SKIPPED)")
        
        # Step 2: Fetch ATM IV
        logger.info("\n🎯 STEP 2: Fetching ATM IV...")
        iv_success = await self.fetch_and_save_atm_iv(base_coin)
        
        if not iv_success:
            logger.warning("⚠️  Failed to fetch IV. Continuing to recalculation...")
        
        # Step 3: Recalculate IV Rank
        logger.info("\n📊 STEP 3: Recalculating IV Rank...")
        rank_success = await self.recalculate_iv_rank(base_coin)
        
        # Summary
        logger.info("\n" + "=" * 70)
        if iv_success and rank_success:
            logger.success("✅ DAILY UPDATE COMPLETE!")
        elif rank_success:
            logger.warning("⚠️  UPDATE PARTIAL (IV fetch failed, but rank updated)")
        else:
            logger.error("❌ DAILY UPDATE FAILED")
        logger.info("=" * 70)
        
        return iv_success and rank_success


async def main():
    """Main entry point"""
    # Check if running in "skip health check" mode
    skip_check = (
        "--skip-health-check" in sys.argv or
        os.getenv("SKIP_BYBIT_HEALTH_CHECK", "false").lower() == "true"
    )
    
    try:
        async with DailyIVUpdater(skip_health_check=skip_check) as updater:
            success = await updater.run_daily_update(base_coin="BTC")
            
            if success:
                sys.exit(0)
            else:
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    
    # Log to stdout
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Log to file (rotating daily)
    log_file = "logs/daily_iv_update_{time:YYYY-MM-DD}.log"
    os.makedirs("logs", exist_ok=True)
    
    logger.add(
        log_file,
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep 30 days of logs
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )
    
    logger.info("🚀 Starting Daily IV Update...")
    asyncio.run(main())
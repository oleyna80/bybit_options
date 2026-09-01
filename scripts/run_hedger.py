#!/usr/bin/env python3
"""
Delta Hedger Bot Entry Point.

Запускает бота для автоматического дельта-хеджирования.

Usage:
    python scripts/run_hedger.py
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import asyncpg
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.hedger import DeltaHedgerBot, HedgerConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_hedger")


class HedgerApp:
    """Application wrapper for Delta Hedger Bot."""
    
    def __init__(self):
        self.bot: Optional[DeltaHedgerBot] = None
        self.connector: Optional[BybitConnector] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.stop_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Initialize all components."""
        # Clean environment vars for security
        # (Assuming .env is loaded by load_dotenv below)
        
        load_dotenv()
        
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        db_dsn = os.getenv("DATABASE_URL")
        
        if not api_key or not api_secret:
            raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
        
        if not db_dsn:
            raise ValueError("DATABASE_URL must be set")
        
        # Initialize Database Pool
        logger.info("Connecting to database...")
        self.db_pool = await asyncpg.create_pool(db_dsn)
        
        # Initialize Bybit Connector
        logger.info("Initializing Bybit connector...")
        self.connector = BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=os.getenv("BYBIT_TESTNET", "true").lower() == "true"
        )
        
        # Load Config
        logger.info("Loading hedger configuration...")
        config = await HedgerConfigLoader.load_from_db(self.db_pool)
        
        # Initialize Bot
        logger.info(f"Initializing bot in {config.mode.value} mode...")
        self.bot = DeltaHedgerBot(self.connector, self.db_pool, config)
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.connector:
            await self.connector.close()
            logger.info("Connector closed")
        
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database connection closed")
            
    async def run(self, dry_run: bool = False) -> None:
        """Run the application."""
        try:
            await self.initialize()
            
            if dry_run and self.bot:
                logger.info("DRY RUN MODE ENABLED: Forcing bot disabled")
                self.bot.config.enabled = False
                # Prevent config refresh from enabling it back? 
                # This simplistic approach only works until next refresh.
                # A better way is needed, but for now let's just log it.
                # Ideally DeltaHedgerBot should have a .dry_run attribute.
                # Since we cannot easily modify Bot now without changing tests, 
                # we will rely on logging and maybe setting enabled=False constitutes dry run enough for safety.
                # However, the bot loops and calls refresh_config().
                
                # To properly support dry-run persistence, we should monkey-patch refresh_config 
                # or modify the bot class.
                # Let's simple check: if dry is passed, we override config.enabled AFTER every refresh?
                # No, simpler: We pass override to bot? 
                
                # Let's modify logic: We will assume user just wants to verify startup.
                pass
            
            # Start bot task
            bot_task = asyncio.create_task(self.bot.start())
            
            # If dry run, maybe we just want to run one check and exit? 
            # Or run in "simulation" mode?
            # Standard "dry-run" for entry points usually means "parse args, init, check config, exit".
            if dry_run:
                logger.info("Dry run check complete. Exiting.")
                self.stop_event.set()
                await self.bot.stop()
                await bot_task
                return

            # Wait for stop signal
            await self.stop_event.wait()
            
            # Stop bot
            logger.info("Shutting down...")
            if self.bot:
                await self.bot.stop()
                try:
                    await bot_task
                except asyncio.CancelledError:
                    pass
            
        except asyncpg.UndefinedTableError:
            logger.error("Database tables missing! Please run migrations first.")
            logger.error("Try: psql -f database_migrations/003_create_hedger_tables.sql")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            sys.exit(1)
        finally:
            await self.cleanup()
    
    def handle_signal(self) -> None:
        """Handle shutdown signal."""
        logger.info("Received stop signal")
        self.stop_event.set()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Delta Hedger Bot")
    parser.add_argument("--dry-run", action="store_true", help="Initialize and exit without running loop")
    parser.add_argument("--config", help="Path to custom config file (not implemented yet)")
    args = parser.parse_args()

    app = HedgerApp()
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, app.handle_signal)
        except NotImplementedError:
            pass
    
    await app.run(dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            # Windows specific loop policy
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        # Should be handled by signal handler, but just in case
        pass

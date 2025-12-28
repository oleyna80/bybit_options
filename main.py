"""
Main CLI Entry Point
Run this to execute the risk analysis
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# === Принудительно включить UTF-8 для Windows консоли ===
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
# =========================================================

from bybit_connector import BybitConnector
from analysis_orchestrator import AnalysisOrchestrator
from display_manager import DisplayManager


def setup_logging(level: str = "INFO"):
    """Configure logging for the application"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Reduce noise from aiohttp
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


async def main():
    """
    Main execution flow
    
    This simulates what a FastAPI endpoint would do:
    1. Initialize services
    2. Run analysis
    3. Return/display results
    """
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env")
        sys.exit(1)
    
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Bybit Options Risk Analysis")
    
    try:
        # Initialize connector with context manager
        async with BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=False,
            rate_limit=50
        ) as connector:
            
            # Create orchestrator
            orchestrator = AnalysisOrchestrator(connector)
            
            # Run analysis
            logger.info("Running full analysis...")
            portfolio = await orchestrator.run_full_analysis(
                fetch_enhanced_metrics=True
            )
            
            # Display results
            logger.info("Displaying results...\n")
            
            display = DisplayManager()
            
            # Show all positions
            all_positions = []
            for coin_risk in portfolio.coin_risks.values():
                all_positions.extend(coin_risk.positions)
            
            display.print_positions_table(all_positions)
            
            # === СОХРАНЕНИЕ ОТЧЕТА В MARKDOWN ===
            report_path = display.save_report_to_markdown(all_positions, portfolio)
            logger.info(f"💾 Report saved to: {report_path}")
            logger.info(f"   (Use 'reports/latest_analysis.md' for AI analysis)")
            # =====================================
            
            logger.info("✅ Analysis complete!")
            
            # In production, this would be:
            # return portfolio.dict()  # FastAPI would serialize to JSON
    
    except KeyboardInterrupt:
        logger.info("⚠️  Analysis interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
#!/usr/bin/env python3
"""Fractal Enricher CLI - runs enrichment cycle."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from bybit_options.services.delta.enricher import FractalEnricher
from bybit_options.services.delta.database_config import db


async def main():
    """Run one enrichment cycle."""
    try:
        await db.connect()
        
        enricher = FractalEnricher()
        stats = await enricher.run_once()
        
        logger.info(f"📊 Stats: {stats}")
        
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
